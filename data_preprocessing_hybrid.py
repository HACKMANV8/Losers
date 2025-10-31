import json
import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
import argparse
from pathlib import Path
import joblib # For saving/loading scaler

# --- Configuration Constants ---
MAX_PASS_SEQ_LEN = 60 # Increased max length for combined common and machine passes
TARGET_METRICS = ['execution_time', 'binary_size'] # Metrics to be predicted

# --- Preprocessing Functions ---

def clean_and_tag_passes(pass_str, hardware_prefix=None):
    """
    Cleans a comma-separated or space-separated pass string into a list of strings.
    Replaces null/empty with ["none"].
    If hardware_prefix is provided, tags each machine pass with it.
    """
    if pass_str is None or (isinstance(pass_str, str) and pass_str.strip() == ""):
        return ["none"]
    
    passes = []
    if isinstance(pass_str, list):
        passes = [p.strip() for p in pass_str if p.strip()]
    elif isinstance(pass_str, str):
        if ',' in pass_str:
            passes = [p.strip() for p in pass_str.split(',') if p.strip()]
        else:
            passes = [p.strip() for p in pass_str.split(' ') if p.strip()]
    
    if not passes:
        return ["none"]
    
    # Add hardware prefix if provided
    if hardware_prefix:
        return [f"{hardware_prefix}::{p}" for p in passes]
    return passes

def build_vocabularies(data_entries):
    """
    Builds a joint vocabulary for all passes (common and tagged machine) and hardware types.
    """
    joint_pass_vocab = {"<pad>": 0, "<unk>": 1, "<sos>": 2, "<eos>": 3}
    hardware_vocab = {"<unk>": 0} # Add <unk> for hardware

    joint_pass_idx = len(joint_pass_vocab)
    hardware_idx = len(hardware_vocab)

    for entry in data_entries:
        # Common Passes
        common_passes = clean_and_tag_passes(entry.get('common_passes'))
        for p in common_passes:
            if p not in joint_pass_vocab:
                joint_pass_vocab[p] = joint_pass_idx
                joint_pass_idx += 1
        
        # Machine Passes (tagged)
        hardware = entry.get('hardware')
        hardware_prefix = hardware.lower() if hardware else "default_hardware"
        machine_passes = clean_and_tag_passes(entry.get('machine_passes'), hardware_prefix=hardware_prefix)
        for p in machine_passes:
            if p not in joint_pass_vocab:
                joint_pass_vocab[p] = joint_pass_idx
                joint_pass_idx += 1
        
        # Hardware
        if hardware and hardware not in hardware_vocab:
            hardware_vocab[hardware] = hardware_idx
            hardware_idx += 1
        elif not hardware and "default_hardware" not in hardware_vocab: # Add default if hardware is missing
            hardware_vocab["default_hardware"] = hardware_idx
            hardware_idx += 1
            
    print(f"Joint Pass Vocab Size: {len(joint_pass_vocab)}")
    print(f"Hardware Vocab Size: {len(hardware_vocab)}")
    print(f"Hardware Vocab: {hardware_vocab}")
    
    return joint_pass_vocab, hardware_vocab

def tokenize_and_pad(sequence_list, vocab, max_len):
    """Converts a list of pass names to token IDs, adds SOS/EOS, and pads/truncates."""
    token_ids = [vocab["<sos>"]]
    token_ids.extend([vocab.get(p, vocab["<unk>"]) for p in sequence_list])
    token_ids.append(vocab["<eos>"])

    if len(token_ids) < max_len:
        token_ids.extend([vocab["<pad>"]] * (max_len - len(token_ids)))
    else:
        token_ids = token_ids[:max_len]
        token_ids[-1] = vocab["<eos>"] # Ensure EOS is at the end if truncated

    return torch.tensor(token_ids, dtype=torch.long)


def load_and_preprocess_data(json_data_path, max_seq_len=MAX_PASS_SEQ_LEN, target_metrics=TARGET_METRICS):
    """
    Loads raw JSON data, builds vocabularies, tokenizes, encodes, and normalizes features.
    Returns processed samples, scaler, feature keys, and vocabularies.
    """
    with open(json_data_path, 'r') as f:
        raw_data_entries = json.load(f)

    print(f"Loaded {len(raw_data_entries)} raw data entries.")

    # Build vocabularies (first pass to collect all unique passes and hardware)
    joint_pass_vocab, hardware_vocab = build_vocabularies(raw_data_entries)

    # Discover all feature keys that start with "feature_"
    all_feature_keys = set()
    for entry in raw_data_entries:
        for k in entry.keys():
            if k.startswith("feature_"):
                all_feature_keys.add(k)
    feature_keys = sorted(list(all_feature_keys))
    print(f"Discovered {len(feature_keys)} program features.")

    processed_samples = []
    
    # First pass to collect features for scaler fitting and target metrics for their own scaler
    program_features_for_scaler = []
    target_metrics_for_scaler = []

    for entry in raw_data_entries:
        program_feature_vector = [entry.get(k, 0.0) for k in feature_keys]
        program_features_for_scaler.append(program_feature_vector)
        
        # Collect target metrics for scaling
        metrics_vector = [float(entry.get(metric, 0.0)) for metric in target_metrics]
        target_metrics_for_scaler.append(metrics_vector)

    # Fit and transform program features
    feature_scaler = StandardScaler()
    if program_features_for_scaler:
        scaled_features = feature_scaler.fit_transform(np.array(program_features_for_scaler, dtype=np.float32))
    else:
        scaled_features = np.array([], dtype=np.float32).reshape(0, len(feature_keys))
    print("Program features scaler fitted.")

    # Fit and transform target metrics
    target_metric_scaler = StandardScaler()
    if target_metrics_for_scaler:
        scaled_target_metrics = target_metric_scaler.fit_transform(np.array(target_metrics_for_scaler, dtype=np.float32))
    else:
        scaled_target_metrics = np.array([], dtype=np.float32).reshape(0, len(target_metrics))
    print("Target metrics scaler fitted.")

    # Second pass to process all data
    for i, entry in enumerate(raw_data_entries):
        hardware = entry.get('hardware')
        hardware_prefix = hardware.lower() if hardware else "default_hardware"

        # Clean common passes
        common_passes_list = clean_and_tag_passes(entry.get('common_passes'))
        
        # Clean and tag machine passes
        machine_passes_list = clean_and_tag_passes(entry.get('machine_passes'), hardware_prefix=hardware_prefix)
        
        # Combine common and tagged machine passes
        unified_pass_sequence = common_passes_list + machine_passes_list
        
        # Tokenize and pad the unified sequence
        unified_pass_sequence_tensor = tokenize_and_pad(unified_pass_sequence, joint_pass_vocab, max_seq_len)

        # Encode hardware
        hardware_id = hardware_vocab.get(hardware, hardware_vocab["default_hardware"])
        hardware_tensor = torch.tensor(hardware_id, dtype=torch.long)

        # Use already scaled program features
        program_feature_tensor = torch.tensor(scaled_features[i], dtype=torch.float32)

        # Use already scaled target metrics
        labels_tensor = torch.tensor(scaled_target_metrics[i], dtype=torch.float32)

        processed_samples.append({
            'program_features': program_feature_tensor,
            'hardware_id': hardware_tensor,
            'pass_sequence': unified_pass_sequence_tensor, # Renamed for clarity
            'labels': labels_tensor
        })
    
    print(f"Processed {len(processed_samples)} samples.")

    return processed_samples, feature_scaler, feature_keys, joint_pass_vocab, hardware_vocab, target_metric_scaler

# --- Main Execution ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess NeuroOpt hybrid training data.")
    parser.add_argument("--input_json", type=str, required=True,
                        help="Path to the input flattened JSON dataset (e.g., new_flattened_hybrid_data.json).")
    parser.add_argument("--output_dir", type=str, default="preprocessing_output",
                        help="Directory to save vocabularies, scaler, and feature keys.")
    
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Starting data preprocessing for {args.input_json}...")
    processed_samples, feature_scaler, feature_keys, joint_pass_vocab, hardware_vocab, target_metric_scaler = \
        load_and_preprocess_data(args.input_json)

    # --- Save Preprocessing Artifacts ---
    with open(output_path / "joint_pass_vocab.json", 'w') as f:
        json.dump(joint_pass_vocab, f, indent=2)
    with open(output_path / "hardware_vocab.json", 'w') as f:
        json.dump(hardware_vocab, f, indent=2)
    joblib.dump(feature_scaler, output_path / "feature_scaler.pkl")
    joblib.dump(target_metric_scaler, output_path / "target_metric_scaler.pkl")
    with open(output_path / "feature_keys.json", 'w') as f:
        json.dump(feature_keys, f, indent=2)
    
    print(f"Preprocessing complete. Artifacts saved to {output_path}")
    print("You can now use these artifacts and the processed_samples (if returned) for model training.")

    # Example of how to use processed_samples with a PyTorch DataLoader
    # from torch.utils.data import TensorDataset, DataLoader
    # # Convert list of dicts to dict of lists/tensors
    # pf = torch.stack([s['program_features'] for s in processed_samples])
    # hid = torch.stack([s['hardware_id'] for s in processed_samples])
    # ps = torch.stack([s['pass_sequence'] for s in processed_samples])
    # lbl = torch.stack([s['labels'] for s in processed_samples])
    # 
    # dataset = TensorDataset(pf, hid, ps, lbl)
    # dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    # print(f"Example DataLoader batch shape: {next(iter(dataloader))[0].shape}")