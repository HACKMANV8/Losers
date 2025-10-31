
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
                predicted_passes = beam_search_decode(
                    runtime_model,
                    extracted_features['features'], # Pass the actual features dictionary
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
                    'features': extracted_features['features'],
                    'processing_time_ms': (time.time() - start_time) * 1000,
                    'error': f"Transformer model inference failed: {str(e)}"
                }), 500
        elif model_selection == 'xgboost':
            if xgboost_model is None:
                return jsonify({
                    'success': False,
                    'model_used': 'xgboost',
                    'predicted_passes': None,
                    'features': extracted_features['features'],
                    'processing_time_ms': (time.time() - start_time) * 1000,
                    'error': 'XGBoost model is not available.'
                }), 503 # Service Unavailable

            try:
                # Convert features to a pandas DataFrame in the correct order
                features_df = pd.DataFrame([extracted_features['features']], columns=runtime_feature_keys)
                
                # Run XGBoost inference
                # The prediction is assumed to be a string of space-separated pass names
                prediction_str = xgboost_model.predict(features_df)[0]
                predicted_passes = prediction_str.split()

            except Exception as e:
                return jsonify({
                    'success': False,
                    'model_used': 'xgboost',
                    'predicted_passes': None,
                    'features': extracted_features['features'],
                    'processing_time_ms': (time.time() - start_time) * 1000,
                    'error': f"XGBoost model inference failed: {str(e)}"
                }), 500

        # 4. Return Standardized Response
        return jsonify({
            'success': True,
            'model_used': model_selection,
            'predicted_passes': predicted_passes,
            'features': extracted_features['features'],
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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
