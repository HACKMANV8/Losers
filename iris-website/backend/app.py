
from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
import sys
import os
import numpy as np
import json
import time
import tempfile
import pandas as pd
import joblib
import logging
from datetime import datetime

# Add the parent directory to the Python path to allow importing iris
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from iris import load_model, beam_search_decode

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# --- Load Model and Data ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Construct absolute paths to model and data files
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
runtime_model_path = os.path.join(base_dir, 'passformer_binary_size.pth')
data_path = os.path.join(base_dir, 'tools', 'training_data', 'training_data_flat.json')

runtime_model, runtime_vocab, runtime_feature_keys, runtime_feature_scaler = load_model(runtime_model_path, device)

with open(data_path, 'r') as f:
    training_data = json.load(f)

# Create a dictionary to easily access program features
program_features = {entry['program']: entry['program_features'] for entry in training_data}
program_names = list(program_features.keys())

# --- Load XGBoost Model ---
xgboost_model_path = os.path.join(base_dir, 'models', 'combined_model.pkl')
xgboost_model = None
if os.path.exists(xgboost_model_path):
    try:
        xgboost_model = joblib.load(xgboost_model_path)
    except Exception as e:
        print(f"Warning: Failed to load XGBoost model: {e}")

@app.route('/')
def home():
    return "Hello, from the IRis backend!"

@app.route('/programs', methods=['GET'])
def get_programs():
    return jsonify(program_names)

@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.get_json()
    program_name = data.get('program')

    if not program_name or program_name not in program_features:
        return jsonify({'error': 'Invalid program name'}), 400

    features = program_features[program_name]
    
    # Convert features to a numpy array in the correct order
    try:
        generated_sequence = beam_search_decode(runtime_model, features, runtime_feature_keys, runtime_feature_scaler, runtime_vocab, device)
    except Exception as e:
        return jsonify({
            'success': False,
            'model_used': 'transformer',
            'predicted_passes': None,
            'features': features,
            'processing_time_ms': 0.0, # Placeholder, will be calculated in the full endpoint
            'error': f"Model inference failed: {str(e)}"
        }), 500

    # For now, we return a dummy reference sequence
    dummy_reference_sequence = [
        '-deadargelim',
        '-reassociate',
        '-sccp',
        '-mem2reg',
        '-argpromotion',
    ]

    return jsonify({
        'success': True,
        'model_used': 'transformer',
        'predicted_passes': generated_sequence,
        'features': features,
        'processing_time_ms': 0.0, # Placeholder, will be calculated in the full endpoint
        'error': None
    })

from tools.feature_extractor import extract_features_from_c_source
from compilation_pipeline import CompilationPipeline, calculate_improvements

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize compilation pipeline (RISC-V target)
compilation_pipeline = CompilationPipeline(target_arch="riscv64", use_qemu=True)
logger.info("Compilation pipeline initialized for RISC-V (riscv64)")

@app.route('/api/optimize', methods=['POST'])
def api_optimize():
    start_time = time.time()
    
    # 1. Input Validation
    if 'source_file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No source file provided.',
            'processing_time_ms': (time.time() - start_time) * 1000
        }), 400

    file = request.files['source_file']
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No selected file.',
            'processing_time_ms': (time.time() - start_time) * 1000
        }), 400

    allowed_extensions = {'c', 'cpp'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({
            'success': False,
            'error': 'Invalid file type. Please upload a .c or .cpp file.',
            'processing_time_ms': (time.time() - start_time) * 1000
        }), 400

    model_selection = request.form.get('model_selection')
    if model_selection not in ['transformer', 'xgboost']:
        return jsonify({
            'success': False,
            'error': 'Invalid model selection. Please choose \'transformer\' or \'xgboost\'.',
            'processing_time_ms': (time.time() - start_time) * 1000
        }), 400

    temp_file_path = None
    try:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.c') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name

        # 2. Feature Extraction
        try:
            # Assuming extract_features_from_c_source can handle the target_arch
            # For now, we'll use 'riscv64' as default, but this could be an input parameter
            # Note: extract_features_from_c_source returns features dict directly
            extracted_features = extract_features_from_c_source(temp_file_path, target_arch='riscv64')
        except RuntimeError as e:
            return jsonify({
                'success': False,
                'model_used': model_selection,
                'predicted_passes': None,
                'features': None,
                'processing_time_ms': (time.time() - start_time) * 1000,
                'error': f"Feature extraction failed: {str(e)}"
            }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'model_used': model_selection,
                'predicted_passes': None,
                'features': None,
                'processing_time_ms': (time.time() - start_time) * 1000,
                'error': f"An unexpected error occurred during feature extraction: {str(e)}"
            }), 500

        # 3. Model Routing and Prediction
        predicted_passes = []
        if model_selection == 'transformer':
            try:
                # The beam_search_decode function now expects raw_features_dict and feature_keys
                # extracted_features is already the features dict (not wrapped)
                predicted_passes = beam_search_decode(
                    runtime_model,
                    extracted_features,  # Pass the features dictionary directly
                    runtime_feature_keys,
                    runtime_feature_scaler,
                    runtime_vocab,
                    device
                )
            except Exception as e:
                return jsonify({
                    'success': False,
                    'model_used': 'transformer',
                    'predicted_passes': None,
                    'features': extracted_features,
                    'processing_time_ms': (time.time() - start_time) * 1000,
                    'error': f"Transformer model inference failed: {str(e)}"
                }), 500
        elif model_selection == 'xgboost':
            if xgboost_model is None:
                return jsonify({
                    'success': False,
                    'model_used': 'xgboost',
                    'predicted_passes': None,
                    'features': extracted_features,
                    'processing_time_ms': (time.time() - start_time) * 1000,
                    'error': 'XGBoost model is not available.'
                }), 503 # Service Unavailable

            try:
                # Convert features to a pandas DataFrame in the correct order
                features_df = pd.DataFrame([extracted_features], columns=runtime_feature_keys)
                
                # Run XGBoost inference
                # The prediction is assumed to be a string of space-separated pass names
                prediction_str = xgboost_model.predict(features_df)[0]
                predicted_passes = prediction_str.split()

            except Exception as e:
                return jsonify({
                    'success': False,
                    'model_used': 'xgboost',
                    'predicted_passes': None,
                    'features': extracted_features,
                    'processing_time_ms': (time.time() - start_time) * 1000,
                    'error': f"XGBoost model inference failed: {str(e)}"
                }), 500

        # 4. Return Standardized Response
        return jsonify({
            'success': True,
            'model_used': model_selection,
            'predicted_passes': predicted_passes,
            'features': extracted_features,
            'processing_time_ms': (time.time() - start_time) * 1000,
            'error': None
        }), 200

    except Exception as e:
        # Catch any other unexpected errors
        return jsonify({
            'success': False,
            'error': f"An unexpected server error occurred: {str(e)}",
            'processing_time_ms': (time.time() - start_time) * 1000
        }), 500
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.route('/api/compare', methods=['POST'])
def api_compare():
    """
    Compare ML-predicted pass sequences against standard LLVM optimization levels.
    
    Expects:
    - source_file: C/C++ source file (multipart/form-data)
    - predicted_passes: JSON string array of pass names
    - optimization_levels: Optional JSON array (default: ["-O0", "-O2", "-O3", "-Oz"])
    - num_runs: Optional integer (default: 5)
    
    Returns:
    - Comparison results with metrics for each method
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("New comparison request received")
    
    # 1. Input Validation
    if 'source_file' not in request.files:
        logger.error("No source file provided")
        return jsonify({
            'success': False,
            'error': 'No source file provided.',
            'processing_time_ms': (time.time() - start_time) * 1000
        }), 400
    
    file = request.files['source_file']
    if file.filename == '':
        logger.error("Empty filename")
        return jsonify({
            'success': False,
            'error': 'No selected file.',
            'processing_time_ms': (time.time() - start_time) * 1000
        }), 400
    
    # Validate file type
    allowed_extensions = {'c', 'cpp'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        logger.error(f"Invalid file type: {file.filename}")
        return jsonify({
            'success': False,
            'error': 'Invalid file type. Please upload a .c or .cpp file.',
            'processing_time_ms': (time.time() - start_time) * 1000
        }), 400
    
    logger.info(f"File received: {file.filename}")
    
    # Get predicted passes
    try:
        predicted_passes_str = request.form.get('predicted_passes', '[]')
        predicted_passes = json.loads(predicted_passes_str)
        if not isinstance(predicted_passes, list):
            raise ValueError("predicted_passes must be an array")
        logger.info(f"Predicted passes: {predicted_passes}")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Invalid predicted_passes: {e}")
        return jsonify({
            'success': False,
            'error': 'Invalid predicted_passes format. Must be JSON array of strings.',
            'processing_time_ms': (time.time() - start_time) * 1000
        }), 400
    
    # Get optimization levels to compare
    try:
        opt_levels_str = request.form.get('optimization_levels', '["-O0", "-O2", "-O3", "-Oz"]')
        opt_levels = json.loads(opt_levels_str)
        if not isinstance(opt_levels, list):
            raise ValueError("optimization_levels must be an array")
        logger.info(f"Optimization levels to compare: {opt_levels}")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Invalid optimization_levels: {e}")
        return jsonify({
            'success': False,
            'error': 'Invalid optimization_levels format. Must be JSON array of strings.',
            'processing_time_ms': (time.time() - start_time) * 1000
        }), 400
    
    # Get number of runs
    try:
        num_runs = int(request.form.get('num_runs', 5))
        if num_runs < 1 or num_runs > 20:
            raise ValueError("num_runs must be between 1 and 20")
        logger.info(f"Number of runs: {num_runs}")
    except ValueError as e:
        logger.error(f"Invalid num_runs: {e}")
        return jsonify({
            'success': False,
            'error': 'Invalid num_runs. Must be integer between 1 and 20.',
            'processing_time_ms': (time.time() - start_time) * 1000
        }), 400
    
    # Read source code
    try:
        source_code = file.read().decode('utf-8')
        logger.info(f"Source code size: {len(source_code)} bytes, {len(source_code.splitlines())} lines")
    except Exception as e:
        logger.error(f"Failed to read source file: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to read source file: {str(e)}',
            'processing_time_ms': (time.time() - start_time) * 1000
        }), 400
    
    # 2. Run Compilations
    results = {}
    
    # Compile with ML-predicted passes
    logger.info("[1/N] Compiling with ML-predicted passes...")
    ml_start = time.time()
    try:
        ml_result = compilation_pipeline.compile_with_ml_passes(
            source_code=source_code,
            predicted_passes=predicted_passes,
            num_runs=num_runs,
            timeout=10
        )
        ml_time = time.time() - ml_start
        logger.info(f"ML compilation {'succeeded' if ml_result['success'] else 'failed'} in {ml_time:.2f}s")
        if ml_result['success']:
            logger.info(f"  Binary: {ml_result['binary_size_human']}, Runtime: {ml_result['runtime_mean']:.4f}s")
        else:
            logger.warning(f"  Error: {ml_result['error']}")
        results['ml_predicted'] = ml_result
    except Exception as e:
        logger.error(f"ML compilation exception: {e}")
        results['ml_predicted'] = {
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'compilation_time': time.time() - ml_start
        }
    
    # Compile with each optimization level
    for idx, opt_level in enumerate(opt_levels, start=2):
        logger.info(f"[{idx}/{len(opt_levels)+1}] Compiling with {opt_level}...")
        opt_start = time.time()
        
        try:
            opt_result = compilation_pipeline.compile_with_optimization_level(
                source_code=source_code,
                opt_level=opt_level,
                num_runs=num_runs,
                timeout=10
            )
            opt_time = time.time() - opt_start
            logger.info(f"{opt_level} compilation {'succeeded' if opt_result['success'] else 'failed'} in {opt_time:.2f}s")
            if opt_result['success']:
                logger.info(f"  Binary: {opt_result['binary_size_human']}, Runtime: {opt_result['runtime_mean']:.4f}s")
            else:
                logger.warning(f"  Error: {opt_result['error']}")
            
            # Normalize key name (e.g., "-O2" -> "llvm_o2")
            key_name = f"llvm_{opt_level.lower().replace('-', '')}"
            results[key_name] = opt_result
        except Exception as e:
            logger.error(f"{opt_level} compilation exception: {e}")
            key_name = f"llvm_{opt_level.lower().replace('-', '')}"
            results[key_name] = {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'compilation_time': time.time() - opt_start
            }
    
    # 3. Calculate Improvements
    logger.info("Calculating improvements...")
    improvements = {}
    
    if results['ml_predicted']['success']:
        for opt_level in opt_levels:
            key_name = f"llvm_{opt_level.lower().replace('-', '')}"
            if key_name in results and results[key_name]['success']:
                try:
                    improvement = calculate_improvements(
                        results['ml_predicted'],
                        results[key_name]
                    )
                    improvements[f"vs_{opt_level.lower().replace('-', '')}"] = improvement
                    logger.info(f"  vs {opt_level}: Size {improvement['binary_size_reduction_percent']:.2f}%, " + 
                               f"Runtime {improvement['runtime_reduction_percent']:.2f}%")
                except Exception as e:
                    logger.error(f"Failed to calculate improvements vs {opt_level}: {e}")
    
    # 4. Generate Summary
    logger.info("Generating summary...")
    summary = {
        'ml_wins': {'binary_size': 0, 'runtime': 0, 'total': 0, 'out_of': 0},
        'best_binary_size': None,
        'best_runtime': None
    }
    
    # Count ML wins
    for key, improvement in improvements.items():
        if improvement['winner_binary'] == 'ml_predicted':
            summary['ml_wins']['binary_size'] += 1
        if improvement['winner_runtime'] == 'ml_predicted':
            summary['ml_wins']['runtime'] += 1
    
    summary['ml_wins']['total'] = summary['ml_wins']['binary_size'] + summary['ml_wins']['runtime']
    summary['ml_wins']['out_of'] = len(improvements) * 2
    
    # Find best methods
    successful_results = [(name, res) for name, res in results.items() if res.get('success')]
    
    if successful_results:
        # Best binary size
        best_binary = min(successful_results, key=lambda x: x[1]['binary_size'])
        summary['best_binary_size'] = {
            'method': best_binary[0],
            'size': best_binary[1]['binary_size'],
            'size_human': best_binary[1]['binary_size_human']
        }
        
        # Best runtime
        best_runtime = min(successful_results, key=lambda x: x[1]['runtime_mean'])
        summary['best_runtime'] = {
            'method': best_runtime[0],
            'time': best_runtime[1]['runtime_mean']
        }
        
        logger.info(f"Best binary size: {summary['best_binary_size']['method']} ({summary['best_binary_size']['size_human']})")
        logger.info(f"Best runtime: {summary['best_runtime']['method']} ({summary['best_runtime']['time']:.4f}s)")
    
    # 5. Build Response
    total_time = time.time() - start_time
    logger.info(f"Comparison completed in {total_time:.2f}s")
    logger.info(f"ML wins: {summary['ml_wins']['total']}/{summary['ml_wins']['out_of']}")
    logger.info("=" * 60)
    
    response = {
        'success': True,
        'file_name': file.filename,
        'target_architecture': 'riscv64',
        'num_runs': num_runs,
        'timestamp': int(datetime.now().timestamp() * 1000),
        **results,  # ml_predicted, llvm_o0, llvm_o2, llvm_o3, llvm_oz
        'improvements': improvements,
        'summary': summary,
        'total_processing_time': total_time,
        'error': None
    }
    
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=True, port=5001)
