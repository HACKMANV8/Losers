# IRIS Backend - Simplified LLVM Optimization API

## Overview
This is the simplified backend for the IRIS system, providing core functionality for:
- **Feature extraction** from C programs
- **Running ML-generated LLVM passes** and measuring performance
- **Comparing with standard optimizations** (-O0, -O1, -O2, -O3)
- **RISC-V target architecture** support

## Core Components

### 1. `services/llvm_optimization_service.py`
Main service class that provides:
- `extract_features_from_c()` - Extract LLVM IR features from C code
- `run_ml_passes()` - Apply ML-generated optimization passes
- `run_standard_optimizations()` - Run standard -O0/-O1/-O2/-O3
- `compare_with_standard()` - Compare ML optimization with standard levels

### 2. `routes/llvm_api.py`
REST API endpoints:
- `POST /api/llvm/features` - Extract features
- `POST /api/llvm/optimize` - Run ML optimization
- `POST /api/llvm/standard` - Run standard optimizations
- `POST /api/llvm/compare` - Compare ML vs standard
- `GET /api/llvm/health` - Health check

### 3. `app_simplified.py`
Simplified Flask application with only essential routes.

## Quick Start

### 1. Install Dependencies
```bash
pip install flask flask-cors
```

### 2. Start the Server
```bash
python app_simplified.py
```
The server will start on `http://localhost:5000`

### 3. Test the API
```bash
python test_api.py
```

## API Usage Examples

### Extract Features
```python
import requests

response = requests.post(
    "http://localhost:5000/api/llvm/features",
    json={
        "code": "int main() { return 0; }",
        "target_arch": "riscv64"
    }
)
```

### Run ML Optimization
```python
response = requests.post(
    "http://localhost:5000/api/llvm/optimize",
    json={
        "code": "int main() { return 0; }",
        "ir_passes": ["mem2reg", "simplifycfg", "instcombine"],
        "target_arch": "riscv64"
    }
)
```

### Compare with Standard Optimizations
```python
response = requests.post(
    "http://localhost:5000/api/llvm/compare",
    json={
        "code": "int main() { return 0; }",
        "ir_passes": ["mem2reg", "simplifycfg", "instcombine"],
        "target_arch": "riscv64"
    }
)
```

## Response Format

### Feature Extraction Response
```json
{
    "success": true,
    "features": {
        "total_instructions": 42,
        "total_basic_blocks": 5,
        "num_functions": 1,
        ...
    },
    "feature_count": 50
}
```

### Optimization Metrics Response
```json
{
    "success": true,
    "metrics": {
        "execution_time_avg": 0.000123,
        "binary_size": 12345,
        "optimization_time": 0.0234,
        "compile_time": 0.0456,
        "ir_passes": ["mem2reg", "simplifycfg"],
        "pass_count": 2
    }
}
```

### Comparison Response
```json
{
    "success": true,
    "features": {...},
    "ml_optimization": {
        "execution_time_avg": 0.000123,
        "binary_size": 12345
    },
    "standard_optimizations": {
        "-O0": {...},
        "-O1": {...},
        "-O2": {...},
        "-O3": {...}
    },
    "comparison": {
        "-O0": {
            "speedup": 2.5,
            "size_reduction": 0.15,
            "ml_faster": true,
            "ml_smaller": true
        },
        ...
        "vs_best": {
            "best_standard": "-O3",
            "ml_beats_best": true,
            "speedup_vs_best": 1.2
        }
    }
}
```

## Key Features

1. **RISC-V Optimization**: All compilation and optimization targets RISC-V architecture
2. **Feature Extraction**: ~50 LLVM IR features for ML model input
3. **Performance Metrics**: Execution time, binary size, compilation time
4. **Comparative Analysis**: Direct comparison with standard optimization levels
5. **Simple API**: Clean REST API with JSON input/output

## Architecture

```
backend/
├── services/
│   └── llvm_optimization_service.py  # Core optimization logic
├── routes/
│   └── llvm_api.py                   # API endpoints
├── app_simplified.py                  # Flask app
├── test_api.py                       # Test suite
└── README_SIMPLIFIED.md             # This file
```

## Requirements

- Python 3.8+
- LLVM tools (clang, opt, llc)
- RISC-V toolchain (riscv64-linux-gnu-gcc)
- QEMU for RISC-V emulation (qemu-riscv64)

## Notes

- All optimizations target RISC-V architecture
- Uses QEMU for cross-compiled binary execution
- Provides both IR-level and machine-level optimization support
- Simplified from the original complex backend to focus on core functionality
