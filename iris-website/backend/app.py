
from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
import sys
import os
import numpy as np
import json

# Add the parent directory to the Python path to allow importing neuropt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from neuropt import load_model, beam_search_decode

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# --- Load Model and Data ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Construct absolute paths to model and data files
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
runtime_model_path = os.path.join(base_dir, 'passformer_runtime.pth')
data_path = os.path.join(base_dir, 'tools', 'training_data', 'training_data_flat.json')

runtime_model, runtime_vocab, runtime_feature_keys, runtime_feature_scaler = load_model(runtime_model_path, device)

with open(data_path, 'r') as f:
    training_data = json.load(f)

# Create a dictionary to easily access program features
program_features = {entry['program']: entry['program_features'] for entry in training_data}
program_names = list(program_features.keys())

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
    feature_vector = np.array([features.get(k, 0.0) for k in runtime_feature_keys])

    generated_sequence = beam_search_decode(runtime_model, feature_vector, runtime_feature_scaler, runtime_vocab, device)

    # For now, we return a dummy reference sequence
    dummy_reference_sequence = [
        '-deadargelim',
        '-reassociate',
        '-sccp',
        '-mem2reg',
        '-argpromotion',
    ]

    return jsonify({
        'generated_sequence': generated_sequence,
        'reference_sequence': dummy_reference_sequence, # Replace with actual best sequence later
        'features': features
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
