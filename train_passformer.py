
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split
import numpy as np
from sklearn.preprocessing import StandardScaler
import math
import io

# --- Configuration ---
CONFIG = {
    "d_model": 128,
    "nhead": 4,
    "num_decoder_layers": 2,
    "dim_feedforward": 256,
    "feature_mlp_layers": [128, 128],
    "lr": 0.001,
    "epochs": 10,
    "batch_size": 32,
    "target_metric": "runtime",  # "runtime" or "binary_size"
    "max_seq_len": 64,
    "val_split": 0.2,
    "dropout": 0.1,
}

# --- Dummy Data ---
# In a real scenario, this would be loaded from 'tools/training_data/training_data.json'
DUMMY_DATA = """
[
    {
        "program_name": "prog1",
        "features": "loop=10,branch=5,instructions=512,memory_access=128",
        "seq_ids": [0, 1],
        "sequences": [
            ["-mem2reg", "-inline", "-gvn", "-licm"],
            ["-inline", "-gvn", "-sccp", "-adce", "-dse"]
        ],
        "runtimes": [0.41, 0.39],
        "binary_sizes": [12000, 11800]
    },
    {
        "program_name": "prog2",
        "features": "loop=2,branch=2,instructions=128,memory_access=32",
        "seq_ids": [0, 1],
        "sequences": [
            ["-mem2reg", "-sroa", "-early-cse"],
            ["-gvn", "-inline", "-licm", "-mem2reg", "-instcombine"]
        ],
        "runtimes": [0.15, 0.18],
        "binary_sizes": [4500, 4800]
    }
]
"""

# --- Dataset and DataLoader ---

def parse_features(feature_dict):
    """Converts a dictionary of features into a dictionary of floats."""
    return {k: float(v) for k, v in feature_dict.items()}

class PassSequenceDataset(Dataset):
    """
    Dataset for the NeuroOpt task.
    Each sample consists of program features and the best-performing pass sequence.
    """
    def __init__(self, data, target_metric, max_seq_len):
        super().__init__()
        self.target_metric = target_metric
        self.max_seq_len = max_seq_len

        self.samples = []
        self.pass_vocab = {'<pad>': 0, '<unk>': 1, '<sos>': 2, '<eos>': 3}
        self.feature_keys = []

        self._process_data(data)
        self._build_vocab()
        self._tokenize_sequences()

        self.feature_scaler = StandardScaler()
        self._normalize_features()

    def _process_data(self, data):
        """Groups data by program and finds the best sequence for each."""
        if not data:
            return

        # Group samples by program
        programs = {}
        for entry in data:
            prog_name = entry['program']
            if prog_name not in programs:
                programs[prog_name] = []
            programs[prog_name].append(entry)

        # Find the best sequence for each program
        for prog_name, entries in programs.items():
            best_entry = min(entries, key=lambda x: x[self.target_metric])
            
            features = parse_features(best_entry['program_features'])
            if not self.feature_keys:
                self.feature_keys = sorted(features.keys())

            ordered_features = [features.get(k, 0.0) for k in self.feature_keys]

            self.samples.append({
                'features': np.array(ordered_features, dtype=np.float32),
                'sequence': best_entry['pass_sequence']
            })

    def _build_vocab(self):
        """Builds a vocabulary of all unique compiler passes."""
        pass_idx = len(self.pass_vocab)
        for sample in self.samples:
            for p in sample['sequence']:
                if p not in self.pass_vocab:
                    self.pass_vocab[p] = pass_idx
                    pass_idx += 1
        self.vocab_size = len(self.pass_vocab)

    def _tokenize_sequences(self):
        """Converts pass sequences to token IDs with padding/truncation and SOS/EOS."""
        for sample in self.samples:
            seq = sample['sequence']
            token_ids = [self.pass_vocab['<sos>']]
            token_ids.extend([self.pass_vocab.get(p, self.pass_vocab['<unk>']) for p in seq])
            token_ids.append(self.pass_vocab['<eos>'])

            # Pad or truncate
            if len(token_ids) < self.max_seq_len:
                token_ids.extend([self.pass_vocab['<pad>']] * (self.max_seq_len - len(token_ids)))
            else:
                token_ids = token_ids[:self.max_seq_len]
                token_ids[-1] = self.pass_vocab['<eos>'] # Ensure EOS is the last token

            sample['sequence_tokens'] = torch.tensor(token_ids, dtype=torch.long)

    def _normalize_features(self):
        """Fits and transforms program features using StandardScaler."""
        if not self.samples:
            self.num_features = 0
            return
        
        all_features = np.array([s['features'] for s in self.samples])
        self.num_features = all_features.shape[1]
        
        if all_features.size > 0:
            scaled_features = self.feature_scaler.fit_transform(all_features)
            for i, sample in enumerate(self.samples):
                sample['features_scaled'] = torch.tensor(scaled_features[i], dtype=torch.float32)
        else: # Handle case with no features
             for i, sample in enumerate(self.samples):
                sample['features_scaled'] = torch.zeros(self.num_features, dtype=torch.float32)


    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        return (
            sample['features_scaled'],
            sample['sequence_tokens']
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
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)

class PassFormer(nn.Module):
    """
    Transformer-based seq2seq model for NeuroOpt.
    Encoder: MLP processing program features.
    Decoder: Transformer generating a pass sequence.
    """
    def __init__(self, vocab_size, num_features, d_model, nhead, num_decoder_layers,
                 dim_feedforward, feature_mlp_layers, max_seq_len, dropout=0.1):
        super().__init__()
        self.d_model = d_model
        self.pass_embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout, max_seq_len)

        # Encoder (MLP for features)
        mlp_layers = []
        input_dim = num_features
        for layer_dim in feature_mlp_layers:
            mlp_layers.append(nn.Linear(input_dim, layer_dim))
            mlp_layers.append(nn.ReLU())
            mlp_layers.append(nn.Dropout(dropout))
            input_dim = layer_dim
        self.feature_mlp = nn.Sequential(*mlp_layers)

        # Project feature representation to d_model to be used as memory
        self.feature_projection = nn.Linear(input_dim, d_model)

        # Decoder
        decoder_layer = nn.TransformerDecoderLayer(d_model, nhead, dim_feedforward, dropout, batch_first=True)
        self.transformer_decoder = nn.TransformerDecoder(decoder_layer, num_decoder_layers)

        # Output layer
        self.fc_out = nn.Linear(d_model, vocab_size)

    def forward(self, features, target_sequence):
        # Encode features
        feature_representation = self.feature_mlp(features)
        memory = self.feature_projection(feature_representation).unsqueeze(1) # (batch, 1, d_model)

        # Decode sequence
        target_emb = self.pass_embedding(target_sequence) * math.sqrt(self.d_model)
        target_emb = self.pos_encoder(target_emb)

        # Generate a causal mask for the decoder
        target_mask = nn.Transformer.generate_square_subsequent_mask(target_sequence.size(1)).to(features.device)
        
        # Create padding mask for the target sequence
        target_padding_mask = (target_sequence == 0) # Assumes <pad> token is 0

        decoder_output = self.transformer_decoder(
            tgt=target_emb,
            memory=memory,
            tgt_mask=target_mask,
            tgt_key_padding_mask=target_padding_mask
        )

        return self.fc_out(decoder_output)


# --- Training Loop ---

import torch.nn.functional as F

def beam_search_decode(model, features, dataset, device, beam_width=5, max_len=50):
    """Generates a pass sequence using beam search."""
    model.eval()

    # Normalize features
    features = dataset.feature_scaler.transform(features.reshape(1, -1))
    features = torch.tensor(features, dtype=torch.float32).to(device)

    # Start with SOS token
    start_token = dataset.pass_vocab['<sos>']
    end_token = dataset.pass_vocab['<eos>']

    # Initialize beams
    # Each beam is a tuple of (sequence, score)
    beams = [([start_token], 0.0)]

    for _ in range(max_len):
        new_beams = []
        for seq, score in beams:
            if seq[-1] == end_token:
                new_beams.append((seq, score))
                continue

            input_tensor = torch.tensor([seq], dtype=torch.long).to(device)
            with torch.no_grad():
                output_logits = model(features, input_tensor)
            
            # Get the last predicted token probabilities
            log_probs = F.log_softmax(output_logits[0, -1, :], dim=0)
            top_k_log_probs, top_k_indices = torch.topk(log_probs, beam_width)

            for i in range(beam_width):
                new_seq = seq + [top_k_indices[i].item()]
                new_score = score + top_k_log_probs[i].item()
                new_beams.append((new_seq, new_score))

        # Sort all new beams by score and keep the top k
        beams = sorted(new_beams, key=lambda x: x[1], reverse=True)[:beam_width]

    # Return the best sequence
    best_seq, _ = beams[0]
    if best_seq[-1] != end_token:
        best_seq.append(end_token)

    # Convert token IDs back to passes
    id_to_pass = {v: k for k, v in dataset.pass_vocab.items()}
    generated_passes = [id_to_pass.get(tok, '<unk>') for tok in best_seq[1:-1]] # Exclude SOS and EOS
    
    return generated_passes

from nltk.translate.bleu_score import sentence_bleu
from Levenshtein import distance as levenshtein_distance
from scipy.spatial.distance import jaccard

def evaluate_model(model, val_dataset, device):
    """Evaluates the model on the validation set using multiple metrics."""
    model.eval()
    total_bleu_score = 0
    exact_matches = 0
    total_jaccard_similarity = 0
    total_levenshtein_distance = 0
    dataset = val_dataset.dataset

    print("\n--- Model Evaluation (Beam Search) ---")
    for idx in val_dataset.indices:
        original_sample = dataset.samples[idx]
        features = original_sample['features']
        
        generated_sequence = beam_search_decode(model, features, dataset, device)
        reference_sequence = original_sample['sequence']
        
        print(f"Reference sequence: {reference_sequence}")
        print(f"Generated sequence: {generated_sequence}")
        
        # Exact Match
        if generated_sequence == reference_sequence:
            exact_matches += 1

        # Jaccard Similarity
        jaccard_sim = 1 - jaccard(set(reference_sequence), set(generated_sequence))
        total_jaccard_similarity += jaccard_sim

        # Levenshtein Distance
        lev_dist = levenshtein_distance(generated_sequence, reference_sequence)
        total_levenshtein_distance += lev_dist

        # BLEU Score
        bleu_score = sentence_bleu([reference_sequence], generated_sequence)
        total_bleu_score += bleu_score
        
        print(f"BLEU: {bleu_score:.4f}, Jaccard: {jaccard_sim:.4f}, Levenshtein: {lev_dist}")

    num_samples = len(val_dataset)
    avg_bleu_score = total_bleu_score / num_samples
    exact_match_accuracy = exact_matches / num_samples
    avg_jaccard_similarity = total_jaccard_similarity / num_samples
    avg_levenshtein_distance = total_levenshtein_distance / num_samples

    print("\n--- Evaluation Summary ---")
    print(f"Exact Match Accuracy: {exact_match_accuracy:.4f}")
    print(f"Average Jaccard Similarity: {avg_jaccard_similarity:.4f}")
    print(f"Average Levenshtein Distance: {avg_levenshtein_distance:.4f}")
    print(f"Average BLEU score: {avg_bleu_score:.4f}")



def train_model():
    """Main function to orchestrate model training."""
    print("--- NeuroOpt PassFormer Training ---")
    print(f"Configuration: {CONFIG}")

    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load data
    with open('tools/training_data/training_data_flat.json', 'r') as f:
        json_data = json.load(f)

    # Create dataset
    dataset = PassSequenceDataset(
        data=json_data,
        target_metric=CONFIG['target_metric'],
        max_seq_len=CONFIG['max_seq_len']
    )
    
    if len(dataset) == 0:
        print("Dataset is empty. No data to train on. Exiting.")
        return

    # Split data
    val_size = int(len(dataset) * CONFIG['val_split'])
    train_size = len(dataset) - val_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_dataset, batch_size=CONFIG['batch_size'], shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=CONFIG['batch_size'])

    print(f"Vocabulary size: {dataset.vocab_size}")
    print(f"Number of features: {dataset.num_features}")
    print(f"Training on {train_size} samples, validating on {val_size} samples.")

    # Initialize model
    model = PassFormer(
        vocab_size=dataset.vocab_size,
        num_features=dataset.num_features,
        d_model=CONFIG['d_model'],
        nhead=CONFIG['nhead'],
        num_decoder_layers=CONFIG['num_decoder_layers'],
        dim_feedforward=CONFIG['dim_feedforward'],
        feature_mlp_layers=CONFIG['feature_mlp_layers'],
        max_seq_len=CONFIG['max_seq_len'],
        dropout=CONFIG['dropout']
    ).to(device)

    # Loss, optimizer, and scheduler
    loss_fn = nn.CrossEntropyLoss(ignore_index=dataset.pass_vocab['<pad>'])
    optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG['lr'])
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    # Training loop
    for epoch in range(CONFIG['epochs']):
        model.train()
        total_train_loss = 0
        for features, sequences in train_loader:
            features, sequences = features.to(device), sequences.to(device)

            # Prepare decoder input and target
            decoder_input = sequences[:, :-1]
            decoder_target = sequences[:, 1:]

            optimizer.zero_grad()
            predictions = model(features, decoder_input)
            
            # Reshape for loss calculation
            loss = loss_fn(predictions.reshape(-1, dataset.vocab_size), decoder_target.reshape(-1))
            
            loss.backward()
            optimizer.step()

            total_train_loss += loss.item()

        avg_train_loss = total_train_loss / len(train_loader)

        # Validation loop
        model.eval()
        total_val_loss = 0
        with torch.no_grad():
            for features, sequences in val_loader:
                features, sequences = features.to(device), sequences.to(device)

                decoder_input = sequences[:, :-1]
                decoder_target = sequences[:, 1:]

                predictions = model(features, decoder_input)
                loss = loss_fn(predictions.reshape(-1, dataset.vocab_size), decoder_target.reshape(-1))
                total_val_loss += loss.item()

        avg_val_loss = total_val_loss / len(val_loader)
        
        print(f"Epoch {epoch+1}/{CONFIG['epochs']} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
        scheduler.step()

    print("--- Training Complete ---")

    # Save the model and supplementary data
    model_save_path = f'passformer_{CONFIG["target_metric"]}.pth'
    torch.save({
        'model_state_dict': model.state_dict(),
        'vocab': dataset.pass_vocab,
        'feature_keys': dataset.feature_keys,
        'feature_scaler': dataset.feature_scaler,
        'config': CONFIG
    }, model_save_path)
    print(f"Model and data saved to {model_save_path}")

    # --- Example Generation ---
    print("\n--- Example Sequence Generation (Beam Search) ---")
    # Take the first sample from the validation set for demonstration
    first_val_sample_idx = val_dataset.indices[0]
    original_sample = dataset.samples[first_val_sample_idx]
    features = original_sample['features']

    generated_sequence = beam_search_decode(model, features, dataset, device)
    print(f"Generated sequence for a sample program: {generated_sequence}")

    # --- Evaluation ---
    evaluate_model(model, val_dataset, device)


if __name__ == '__main__':
    train_model()
