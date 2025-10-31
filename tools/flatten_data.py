#!/usr/bin/env python3
"""
Flattens the nested training data JSON into a flat JSON and a CSV file.
"""

import json
import pandas as pd
import argparse
from pathlib import Path

def flatten_hybrid_json(data):
    """Flattens the nested hybrid JSON data."""
    flattened_data = []
    for entry in data['data']:
        flat_record = {
            'program': entry['program'],
            'sequence_id': entry['sequence_id'],
            'pass_sequence': ' '.join(entry['ir_passes']),
            'execution_time': entry['execution_time'],
            'binary_size': entry['binary_size'],
        }

        # Flatten features
        for key, value in entry['features'].items():
            flat_record[f'feature_{key}'] = value

        # Flatten machine_config
        for key, value in entry['machine_config'].items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat_record[f'machine_{key}_{sub_key}'] = sub_value
            else:
                flat_record[f'machine_{key}'] = value

        flattened_data.append(flat_record)
    return flattened_data

def main():
    parser = argparse.ArgumentParser(
        description="Flatten the nested training data JSON into a flat JSON and a CSV file."
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input JSON file (e.g., training_data_hybrid.json)",
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help="Path to the directory where the output files will be saved.",
    )
    parser.add_argument(
        "--output-json-name",
        type=str,
        help="Optional: Custom name for the output flattened JSON file.",
    )
    parser.add_argument(
        "--output-csv-name",
        type=str,
        help="Optional: Custom name for the output CSV file.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not output_path.exists():
        output_path.mkdir(parents=True)

    with open(input_path, 'r') as f:
        hybrid_data = json.load(f)

    flattened_data = flatten_hybrid_json(hybrid_data)

    # Save flattened JSON
    flat_json_name = args.output_json_name if args.output_json_name else f"{input_path.stem}_flat.json"
    flat_json_path = output_path / flat_json_name
    with open(flat_json_path, 'w') as f:
        json.dump(flattened_data, f, indent=2)
    print(f"Successfully saved flattened JSON to: {flat_json_path}")

    # Save as CSV
    df = pd.DataFrame(flattened_data)
    csv_name = args.output_csv_name if args.output_csv_name else f"{input_path.stem}.csv"
    csv_path = output_path / csv_name
    df.to_csv(csv_path, index=False)
    print(f"Successfully saved CSV file to: {csv_path}")

if __name__ == "__main__":
    main()
