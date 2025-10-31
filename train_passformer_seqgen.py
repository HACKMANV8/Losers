import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
import numpy as np
import json
import argparse
from pathlib import Path
import math
import os
import joblib # For saving/loading scaler
from data_preprocessing_hybrid import clean_and_tag_passes, build_vocabularies, tokenize_and_pad # Reusing from preprocessing
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

# --- Configuration ---
MAX_PASS_SEQ_LEN = 60 # Max length for combined common and machine passes
TARGET_METRICS = ['execution_time', 'binary_size'] # Metrics to be predicted
D_MODEL = 128         # Embedding dimension
NHEAD = 4             # Number of attention heads
NUM_DECODER_LAYERS = 2 # Number of Transformer decoder layers
DIM_FEEDFORWARD = 256 # Dimension of the feedforward network model in Transformer decoder
FEATURE_MLP_LAYERS = [64, 32] # Hidden layers for program feature MLP
DROPOUT = 0.1

# --- Utility Functions ---

def calculate_ngram_overlap(predicted_sequences, target_sequences, n_grams=[1, 2, 3, 4]):
    overlap_scores = {f'{n}-gram_overlap': 0.0 for n in n_grams}
    total_samples = 0

    for pred_seq, target_seq in zip(predicted_sequences, target_sequences):
        if not target_seq: # Skip empty target sequences
            continue
        total_samples += 1
        
        for n in n_grams:
            pred_ngrams = set(tuple(pred_seq[i:i+n]) for i in range(len(pred_seq) - n + 1))
            target_ngrams = set(tuple(target_seq[i:i+n]) for i in range(len(target_seq) - n + 1))
            
            if len(target_ngrams) == 0:
                overlap_scores[f'{n}-gram_overlap'] += 0.0 # No target n-grams to match
            else:
                overlap = len(pred_ngrams.intersection(target_ngrams))
                overlap_scores[f'{n}-gram_overlap'] += overlap / len(target_ngrams)
    
    for n_gram_key in overlap_scores:
        overlap_scores[n_gram_key] /= total_samples if total_samples > 0 else 1.0

    return overlap_scores

def calculate_bleu_score(predicted_sequences, target_sequences):
    chencherry = SmoothingFunction()
    bleu_scores = []
    for pred_seq, target_seq in zip(predicted_sequences, target_sequences):
        if not target_seq: # Skip empty target sequences
            continue
        # sentence_bleu expects a list of references, and a candidate sentence
        # Each reference is a list of tokens. Candidate is also a list of tokens.
        bleu_scores.append(sentence_bleu([target_seq], pred_seq, smoothing_function=chencherry.method1))
    return sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0.0

# --- Dataset Class ---

class PassGenDataset(Dataset):
    def __init__(self, json_data_path, joint_pass_vocab, hardware_vocab, feature_keys, feature_scaler, max_seq_len, target_metrics):
        with open(json_data_path, 'r') as f:
            raw_data_entries = json.load(f)

        self.samples = []
        self.joint_pass_vocab = joint_pass_vocab
        self.hardware_vocab = hardware_vocab
        self.feature_keys = feature_keys
        self.feature_scaler = feature_scaler
        self.max_seq_len = max_seq_len
        self.target_metrics = target_metrics

        for entry in raw_data_entries:
            hardware = entry.get('hardware')
            hardware_prefix = hardware.lower() if hardware else "unknown"

            # Clean common passes
            common_passes_list = clean_and_tag_passes(entry.get('common_passes'))
            
            # Clean and tag machine passes
            machine_passes_list = clean_and_tag_passes(entry.get('machine_passes'), hardware_prefix=hardware_prefix)
            
            # Combine common and tagged machine passes
            unified_pass_sequence = common_passes_list + machine_passes_list
            
            # Tokenize and pad the unified sequence for input and target
            # Input sequence will have <sos> at the beginning
            input_token_ids = [joint_pass_vocab["<sos>"]]
            input_token_ids.extend([joint_pass_vocab.get(p, joint_pass_vocab["<unk>"]) for p in unified_pass_sequence])
            # Target sequence will have the actual sequence followed by <eos>
            target_token_ids = [joint_pass_vocab.get(p, joint_pass_vocab["<unk>"]) for p in unified_pass_sequence]
            target_token_ids.append(joint_pass_vocab["<eos>"])

            # Pad/truncate to max_seq_len
            if len(input_token_ids) < max_seq_len:
                input_token_ids.extend([joint_pass_vocab["<pad>"]] * (max_seq_len - len(input_token_ids)))
            else:
                input_token_ids = input_token_ids[:max_seq_len]
                # Ensure EOS is at the end if truncated, if it was meant to be there
                if joint_pass_vocab["<eos>"] in input_token_ids:
                    input_token_ids[-1] = joint_pass_vocab["<eos>"]

            if len(target_token_ids) < max_seq_len:
                target_token_ids.extend([joint_pass_vocab["<pad>"]] * (max_seq_len - len(target_token_ids)))
            else:
                target_token_ids = target_token_ids[:max_seq_len]
                target_token_ids[-1] = joint_pass_vocab["<eos>"] # Ensure EOS is at the end if truncated

            input_sequence_tensor = torch.tensor(input_token_ids, dtype=torch.long)
            target_sequence_tensor = torch.tensor(target_token_ids, dtype=torch.long)

            # Encode hardware
            hardware_id = hardware_vocab.get(hardware, hardware_vocab["default_hardware"])
            hardware_tensor = torch.tensor(hardware_id, dtype=torch.long)

            # Extract and scale program features
            program_feature_vector = [entry.get(k, 0.0) for k in feature_keys]
            program_feature_tensor = torch.tensor(self.feature_scaler.transform([program_feature_vector])[0], dtype=torch.float32)

            # Extract labels (runtime, binary_size)
            labels = [float(entry.get(metric, 0.0)) for metric in TARGET_METRICS]
            labels_tensor = torch.tensor(labels, dtype=torch.float32)

            self.samples.append({
                'program_features': program_feature_tensor,
                'hardware_id': hardware_tensor,
                'input_sequence': input_sequence_tensor,
                'target_sequence': target_sequence_tensor,
                'labels': labels_tensor # Add labels to the sample
            })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        return (
            sample['program_features'],
            sample['hardware_id'],
            sample['input_sequence'],
            sample['target_sequence'],
            sample['labels']
        )

# --- Model Architecture ---

class PositionalEncoding(nn.Module):
    """Injects positional information into the input sequence."""
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0) # (1, max_len, d_model)
        self.register_buffer('pe', pe)

    def forward(self, x):
        # x: (batch_size, seq_len, d_model)
        x = x + self.pe[:, :x.size(1)] # Add positional encoding
        return self.dropout(x)

class PassGenTransformer(nn.Module):
    """
    Transformer-based sequence generation model for compiler passes.
    """
    def __init__(self, vocab_size, num_features, hardware_vocab_size, 
                 d_model, nhead, num_decoder_layers, dim_feedforward, feature_mlp_layers, 
                 max_seq_len, dropout=0.1):
        super().__init__()
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        self.vocab_size = vocab_size

        # Embeddings
        self.pass_embedding = nn.Embedding(vocab_size, d_model)
        self.hardware_embedding = nn.Embedding(hardware_vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout, max_seq_len)

        # Program Feature MLP
        mlp_layers = []
        input_dim = num_features
        for layer_dim in feature_mlp_layers:
            mlp_layers.append(nn.Linear(input_dim, layer_dim))
            mlp_layers.append(nn.ReLU())
            mlp_layers.append(nn.Dropout(dropout))
            input_dim = layer_dim
        self.feature_mlp = nn.Sequential(*mlp_layers)
        self.feature_projection = nn.Linear(input_dim, d_model) # Project MLP output to d_model

        # Transformer Decoder
        decoder_layer = nn.TransformerDecoderLayer(d_model, nhead, dim_feedforward, dropout, batch_first=True)
        self.transformer_decoder = nn.TransformerDecoder(decoder_layer, num_decoder_layers)

        # Output layer
        self.output_head = nn.Linear(d_model, vocab_size)

        # Auxiliary Regression Head for Runtime/Binary Size
        self.regression_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, len(TARGET_METRICS)) # Predicts runtime and binary_size
        )

    def forward(self, program_features, hardware_ids, input_sequence):
        # 1. Process Program Features
        feature_representation = self.feature_mlp(program_features)
        feature_proj = self.feature_projection(feature_representation) # (batch_size, d_model)

        hardware_emb = self.hardware_embedding(hardware_ids) # (batch_size, d_model)
        # Add mild Gaussian noise to hardware embeddings during training
        if self.training:
            noise = torch.randn_like(hardware_emb) * 0.01 # Adjust noise scale as needed
            hardware_emb = hardware_emb + noise

        # 3. Combine context for the decoder (program features + hardware embedding)
        # This will serve as the memory for the Transformer Decoder
        context = torch.cat([feature_proj.unsqueeze(1), hardware_emb.unsqueeze(1)], dim=1) # (batch_size, 2, d_model)

        # 4. Process Input Sequence
        input_emb = self.pass_embedding(input_sequence) # (batch_size, seq_len, d_model)
        input_emb = self.pos_encoder(input_emb)

        # 5. Generate target mask for autoregressive decoding
        tgt_mask = nn.Transformer.generate_square_subsequent_mask(input_sequence.size(1)).to(input_sequence.device)

        # 6. Transformer Decoder
        # The context (memory) is passed to the decoder
        decoder_output = self.transformer_decoder(input_emb, context, tgt_mask=tgt_mask) # (batch_size, seq_len, d_model)

        # 7. Output layer
        output = self.output_head(decoder_output) # (batch_size, seq_len, vocab_size)

        # 8. Auxiliary Regression Head
        predicted_metrics = self.regression_head(feature_proj) # (batch_size, len(TARGET_METRICS))

        return output, predicted_metrics

    def generate_sequence_greedy(self, program_features, hardware_ids, start_token, end_token, pad_token, device, max_len=MAX_PASS_SEQ_LEN):
        self.eval()
        batch_size = program_features.size(0)

        # Prepare context
        feature_representation = self.feature_mlp(program_features)
        feature_proj = self.feature_projection(feature_representation) # (batch_size, d_model)
        hardware_emb = self.hardware_embedding(hardware_ids) # (batch_size, d_model)
        context = torch.cat([feature_proj.unsqueeze(1), hardware_emb.unsqueeze(1)], dim=1) # (batch_size, 2, d_model)

        # Initialize input sequence with start token
        # (batch_size, 1) -> (batch_size, max_len) padded with start_token
        input_sequence = torch.full((batch_size, max_len), pad_token, dtype=torch.long, device=device)
        input_sequence[:, 0] = start_token

        # Store generated sequences
        generated_sequences = torch.full((batch_size, max_len), pad_token, dtype=torch.long, device=device)
        generated_sequences[:, 0] = start_token

        for t in range(1, max_len):
            # Get predictions for the current step
            # Use only the generated part of the sequence so far
            current_input = input_sequence[:, :t]
            
            # Generate target mask for autoregressive decoding
            tgt_mask = nn.Transformer.generate_square_subsequent_mask(current_input.size(1)).to(device)

            with torch.no_grad():
                output, _ = self.forward(program_features, hardware_ids, current_input) # (batch_size, current_seq_len, vocab_size)

            # Get the next token (greedy approach)
            next_token_probs = output[:, -1, :] # (batch_size, vocab_size)
            next_tokens = torch.argmax(next_token_probs, dim=-1) # (batch_size)

            # Update input_sequence and generated_sequences
            generated_sequences[:, t] = next_tokens
            if t < max_len - 1:
                input_sequence[:, t] = next_tokens
            
            # Check if all sequences have generated an end_token
            if (next_tokens == end_token).all():
                break
        
        return generated_sequences

# --- Training and Evaluation Functions ---

def train_epoch(model, dataloader, optimizer, criterion, regression_criterion, regression_loss_weight, device, joint_pass_vocab):
    model.train()
    total_loss = 0
    for program_features, hardware_ids, input_sequence, target_sequence, labels in dataloader:
        program_features = program_features.to(device)
        hardware_ids = hardware_ids.to(device)
        input_sequence = input_sequence.to(device)
        target_sequence = target_sequence.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        predictions, predicted_metrics = model(program_features, hardware_ids, input_sequence)

        # Sequence generation loss
        seq_gen_loss = criterion(predictions.view(-1, model.vocab_size), target_sequence.view(-1))
        
        # Regression loss
        reg_loss = regression_criterion(predicted_metrics, labels)

        # Debug printouts
        if program_features.size(0) > 0: # Ensure batch is not empty
            print(f"\n--- Train Epoch Debug (Batch {program_features.size(0)}) ---")
            print(f"Labels (first 5): {labels[:5].tolist()}")
            print(f"Predicted Metrics (first 5): {predicted_metrics[:5].tolist()}")
            print(f"Labels Min/Max: {labels.min().item():.4f} / {labels.max().item():.4f}")
            print(f"Predicted Metrics Min/Max: {predicted_metrics.min().item():.4f} / {predicted_metrics.max().item():.4f}")
            print(f"Labels Mean/Std: {labels.mean().item():.4f} / {labels.std().item():.4f}")
            print(f"Predicted Metrics Mean/Std: {predicted_metrics.mean().item():.4f} / {predicted_metrics.std().item():.4f}")
            print(f"--------------------------------------------------")

        # Combine losses with weighting
        loss = seq_gen_loss + (regression_loss_weight * reg_loss)

        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(dataloader)

def evaluate_epoch(model, dataloader, criterion, regression_criterion, regression_loss_weight, device, joint_pass_vocab):
    model.eval()
    total_loss = 0
    all_predicted_metrics = []
    all_target_labels = []
    with torch.no_grad():
        for program_features, hardware_ids, input_sequence, target_sequence, labels in dataloader:
            program_features = program_features.to(device)
            hardware_ids = hardware_ids.to(device)
            input_sequence = input_sequence.to(device)
            target_sequence = target_sequence.to(device)
            labels = labels.to(device)

            predictions, predicted_metrics = model(program_features, hardware_ids, input_sequence)
            seq_gen_loss = criterion(predictions.view(-1, model.vocab_size), target_sequence.view(-1))
            reg_loss = regression_criterion(predicted_metrics, labels)

            # Debug printouts
            if program_features.size(0) > 0: # Ensure batch is not empty
                print(f"\n--- Eval Epoch Debug (Batch {program_features.size(0)}) ---")
                print(f"Labels (first 5): {labels[:5].tolist()}")
                print(f"Predicted Metrics (first 5): {predicted_metrics[:5].tolist()}")
                print(f"Labels Min/Max: {labels.min().item():.4f} / {labels.max().item():.4f}")
                print(f"Predicted Metrics Min/Max: {predicted_metrics.min().item():.4f} / {predicted_metrics.max().item():.4f}")
                print(f"Labels Mean/Std: {labels.mean().item():.4f} / {labels.std().item():.4f}")
                print(f"Predicted Metrics Mean/Std: {predicted_metrics.mean().item():.4f} / {predicted_metrics.std().item():.4f}")
                print(f"--------------------------------------------------")
            loss = seq_gen_loss + (regression_loss_weight * reg_loss)
            total_loss += loss.item()

            all_predicted_metrics.extend(predicted_metrics.tolist())
            all_target_labels.extend(labels.tolist())

    return total_loss / len(dataloader), all_predicted_metrics, all_target_labels


# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Train PassFormer sequence generation model.")
    parser.add_argument("--input_json", type=str, required=True,
                        help="Path to the input flattened JSON dataset (e.g., new_flattened_hybrid_data.json).")
    parser.add_argument("--output_dir", type=str, default="models_seqgen",
                        help="Directory to save model, vocabularies, and scaler.")
    parser.add_argument("--epochs", type=int, default=10,
                        help="Number of training epochs.")
    parser.add_argument("--batch_size", type=int, default=32,
                        help="Batch size for training.")
    parser.add_argument("--lr", type=float, default=1e-4,
                        help="Learning rate.")
    parser.add_argument("--regression_loss_weight", type=float, default=0.01,
                        help="Weight for the regression loss in the total loss calculation.")
    parser.add_argument("--dry_run", action="store_true",
                        help="Load a few samples and print shapes/tokens without training.")
    
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # --- Load Preprocessing Artifacts ---
    print("Loading preprocessing artifacts...")
    # Assuming these are generated by data_preprocessing_hybrid.py
    try:
        preprocessing_output_path = Path("D:\\Losers\\preprocessing_output")
        with open(preprocessing_output_path / "joint_pass_vocab.json", 'r') as f:
            joint_pass_vocab = json.load(f)
        with open(preprocessing_output_path / "hardware_vocab.json", 'r') as f:
            hardware_vocab = json.load(f)
        feature_scaler = joblib.load(preprocessing_output_path / "feature_scaler.pkl")
        target_metric_scaler = joblib.load(preprocessing_output_path / "target_metric_scaler.pkl")
        with open(preprocessing_output_path / "feature_keys.json", 'r') as f:
            feature_keys = json.load(f)
    except FileNotFoundError:
        print("Error: Preprocessing artifacts not found. Please run data_preprocessing_hybrid.py first.")
        return

    # --- Dataset Creation ---
    print("Creating dataset...")
    full_dataset = PassGenDataset(
        args.input_json,
        joint_pass_vocab,
        hardware_vocab,
        feature_keys,
        feature_scaler,
        MAX_PASS_SEQ_LEN,
        TARGET_METRICS
    )

    # Create train/validation split
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(full_dataset, [train_size, val_size])

    train_dataloader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_dataloader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)

    # --- Model Initialization ---
    print("\nInitializing model...")
    model = PassGenTransformer(
        vocab_size=len(joint_pass_vocab),
        num_features=len(feature_keys),
        hardware_vocab_size=len(hardware_vocab),
        d_model=D_MODEL,
        nhead=NHEAD,
        num_decoder_layers=NUM_DECODER_LAYERS,
        dim_feedforward=DIM_FEEDFORWARD,
        feature_mlp_layers=FEATURE_MLP_LAYERS,
        max_seq_len=MAX_PASS_SEQ_LEN,
        dropout=DROPOUT
    ).to(device)

    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss(ignore_index=joint_pass_vocab["<pad>"]) # Ignore padding in loss
    regression_criterion = nn.MSELoss() # For auxiliary regression head

    print(f"Model parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad)}")

    # --- Training Loop ---
    print("\nStarting training...")
    best_val_loss = float('inf')

    for epoch in range(args.epochs):
        train_loss = train_epoch(model, train_dataloader, optimizer, criterion, regression_criterion, args.regression_loss_weight, device, joint_pass_vocab)
        val_loss, all_predicted_metrics, all_target_labels = evaluate_epoch(model, val_dataloader, criterion, regression_criterion, args.regression_loss_weight, device, joint_pass_vocab)
        print(f"Epoch {epoch+1}/{args.epochs}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

        # Evaluate sequence generation with greedy decoding
        all_predicted_sequences = []
        all_target_sequences = []
        # Note: all_predicted_metrics and all_target_labels are already collected by evaluate_epoch

        for program_features, hardware_ids, input_sequence, target_sequence, _ in val_dataloader: # _ to ignore labels, already collected
            program_features = program_features.to(device)
            hardware_ids = hardware_ids.to(device)
            
            generated_sequences = model.generate_sequence_greedy(
                program_features,
                hardware_ids,
                joint_pass_vocab["<sos>"],
                joint_pass_vocab["<eos>"],
                joint_pass_vocab["<pad>"],
                device,
                MAX_PASS_SEQ_LEN
            )
            all_predicted_sequences.extend(generated_sequences.tolist())
            all_target_sequences.extend(target_sequence.tolist())
        
        # Filter out padding and special tokens for n-gram calculation and BLEU
        filtered_predicted = []
        filtered_target = []
        for pred_seq, target_seq in zip(all_predicted_sequences, all_target_sequences):
            # Convert token IDs back to strings for NLTK BLEU and n-gram overlap
            id_to_pass = {v: k for k, v in joint_pass_vocab.items()}
            
            current_filtered_pred = [id_to_pass.get(token, '<unk>') for token in pred_seq if token not in [joint_pass_vocab["<pad>"], joint_pass_vocab["<sos>"], joint_pass_vocab["<eos>"]]]
            current_filtered_target = [id_to_pass.get(token, '<unk>') for token in target_seq if token not in [joint_pass_vocab["<pad>"], joint_pass_vocab["<sos>"], joint_pass_vocab["<eos>"]]]
            
            filtered_predicted.append(current_filtered_pred)
            filtered_target.append(current_filtered_target)

        ngram_overlap_scores = calculate_ngram_overlap(filtered_predicted, filtered_target, n_grams=[1, 2, 3, 4])
        bleu_score = calculate_bleu_score(filtered_predicted, filtered_target)
        
        print(f"Epoch {epoch+1}/{args.epochs}, BLEU Score: {bleu_score:.4f}")
        for n_gram_key, score in ngram_overlap_scores.items():
            print(f"Epoch {epoch+1}/{args.epochs}, {n_gram_key}: {score:.4f}")

        # Report ground truth and predicted metrics for the validation set
        if all_target_labels and all_predicted_metrics:
            # Inverse transform scaled metrics for display
            all_target_labels_unscaled = target_metric_scaler.inverse_transform(np.array(all_target_labels))
            all_predicted_metrics_unscaled = target_metric_scaler.inverse_transform(np.array(all_predicted_metrics))

            avg_target_runtime = np.mean([l[0] for l in all_target_labels_unscaled])
            avg_target_binary_size = np.mean([l[1] for l in all_target_labels_unscaled])
            avg_predicted_runtime = np.mean([p[0] for p in all_predicted_metrics_unscaled])
            avg_predicted_binary_size = np.mean([p[1] for p in all_predicted_metrics_unscaled])

            runtime_errors = [abs(p[0] - l[0]) for p, l in zip(all_predicted_metrics_unscaled, all_target_labels_unscaled)]
            binary_size_errors = [abs(p[1] - l[1]) for p, l in zip(all_predicted_metrics_unscaled, all_target_labels_unscaled)]
            avg_runtime_error = np.mean(runtime_errors)
            avg_binary_size_error = np.mean(binary_size_errors)

            print(f"Epoch {epoch+1}/{args.epochs}, Avg Target Runtime: {avg_target_runtime:.4f}, Avg Predicted Runtime: {avg_predicted_runtime:.4f}, Runtime MAE: {avg_runtime_error:.4f}")
            print(f"Epoch {epoch+1}/{args.epochs}, Avg Target Binary Size: {avg_target_binary_size:.4f}, Avg Predicted Binary Size: {avg_predicted_binary_size:.4f}, Binary Size MAE: {avg_binary_size_error:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            print("Saving best model...")
            model_save_path = output_path / "passgen_transformer_model_best.pth"
            torch.save({
                'model_state_dict': model.state_dict(),
                'joint_pass_vocab': joint_pass_vocab,
                'hardware_vocab': hardware_vocab,
                'feature_scaler': feature_scaler,
                'feature_keys': feature_keys,
                'config': {
                    'vocab_size': len(joint_pass_vocab),
                    'num_features': len(feature_keys),
                    'hardware_vocab_size': len(hardware_vocab),
                    'd_model': D_MODEL,
                    'nhead': NHEAD,
                    'num_decoder_layers': NUM_DECODER_LAYERS,
                    'dim_feedforward': DIM_FEEDFORWARD,
                    'feature_mlp_layers': FEATURE_MLP_LAYERS,
                    'max_seq_len': MAX_PASS_SEQ_LEN,
                    'dropout': DROPOUT,
                }
            }, model_save_path)

    print("\nTraining complete. Saving final model...")
    
    # --- Save Model and Components ---
    model_save_path = output_path / "passgen_transformer_model_final.pth"
    torch.save({
        'model_state_dict': model.state_dict(),
        'joint_pass_vocab': joint_pass_vocab,
        'hardware_vocab': hardware_vocab,
        'feature_scaler': feature_scaler,
        'feature_keys': feature_keys,
        'config': {
            'vocab_size': len(joint_pass_vocab),
            'num_features': len(feature_keys),
            'hardware_vocab_size': len(hardware_vocab),
            'd_model': D_MODEL,
            'nhead': NHEAD,
            'num_decoder_layers': NUM_DECODER_LAYERS,
            'dim_feedforward': DIM_FEEDFORWARD,
            'feature_mlp_layers': FEATURE_MLP_LAYERS,
            'max_seq_len': MAX_PASS_SEQ_LEN,
            'dropout': DROPOUT,
        }
    }, model_save_path)
    print(f"Final model saved to {model_save_path}")


if __name__ == "__main__":
    main()
