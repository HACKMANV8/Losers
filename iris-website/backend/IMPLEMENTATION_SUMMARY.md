# IRIS Backend Implementation Summary

## Overview
We have successfully implemented a simplified backend API for the IRIS system that provides core functionality for ML-guided LLVM optimization targeting **RISC-V architecture**.

## What We Built

### Core Service: `llvm_optimization_service.py`
A comprehensive service that provides:

1. **Feature Extraction** (`extract_features_from_c`)
   - Extracts 73+ LLVM IR features from C source code
   - Compiles with RISC-V target triple for hardware-specific features
   - Returns features for ML model input

2. **ML Pass Application** (`run_ml_passes`)
   - Applies ML-generated LLVM optimization passes
   - Supports both IR-level passes and machine-level configurations
   - Measures execution time, binary size, and compilation metrics
   - Uses RISC-V GCC toolchain and QEMU for cross-compilation

3. **Standard Optimization Comparison** (`run_standard_optimizations`)
   - Runs standard -O0, -O1, -O2, -O3 optimizations
   - Uses RISC-V GCC for consistent comparison
   - Provides baseline metrics for comparison

4. **Full Comparison Pipeline** (`compare_with_standard`)
   - Runs ML optimization and all standard levels
   - Calculates speedup and size reduction metrics
   - Identifies if ML beats the best standard optimization

### REST API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/llvm/features` | POST | Extract features from C code |
| `/api/llvm/optimize` | POST | Run ML-generated passes |
| `/api/llvm/standard` | POST | Run standard optimizations |
| `/api/llvm/compare` | POST | Compare ML vs standard |
| `/api/llvm/health` | GET | Health check |

### Key RISC-V Specific Features

1. **Target Architecture Support**
   - RISC-V 64-bit (`riscv64-unknown-linux-gnu`)
   - RISC-V 32-bit (`riscv32-unknown-linux-gnu`)
   - Proper floating-point ABI handling (`lp64d`/`ilp32d`)

2. **Compilation Pipeline**
   - Clang with RISC-V target triple for bitcode generation
   - LLVM `opt` for IR-level optimizations
   - LLVM `llc` with RISC-V march for assembly generation
   - RISC-V GCC for executable linking
   - QEMU for cross-compiled binary execution

3. **Optimization Consistency**
   - All optimizations target RISC-V specifically
   - Ensures hardware-specific optimizations are applied
   - Fair comparison between ML and standard optimizations

## Test Results

The API successfully:
- ✅ Extracts 73 features from C programs
- ✅ Applies ML-generated optimization passes
- ✅ Runs standard optimization levels
- ✅ Measures execution time and binary size
- ✅ Compares ML optimization with standard levels
- ✅ Identifies speedup and size reduction

### Example Performance Metrics
From our test suite:
- Feature extraction: ~60ms
- ML optimization: ~200ms (including compilation)
- Execution measurement: 5 runs with QEMU
- Binary sizes: ~556KB for test programs

## Files Created/Modified

### New Files
1. `services/llvm_optimization_service.py` - Core optimization service
2. `routes/llvm_api.py` - REST API endpoints
3. `app_simplified.py` - Simplified Flask application
4. `test_api.py` - Comprehensive test suite
5. `quick_test.py` - Direct service testing
6. `utils/logger_simple.py` - Simple logging utility
7. `README_SIMPLIFIED.md` - API documentation

### Modified Files
1. `services/__init__.py` - Updated imports for simplified service
2. `routes/__init__.py` - Updated imports for simplified routes
3. `utils/__init__.py` - Simplified utility imports

## Usage

### Starting the Server
```bash
cd /home/yash/hackman/iris-website/backend
python3 app_simplified.py
```

### Testing the API
```bash
# Run test suite
python3 test_api.py

# Quick test without API
python3 quick_test.py
```

### Example API Call
```python
import requests

# Extract features
response = requests.post(
    "http://localhost:5000/api/llvm/features",
    json={
        "code": "int main() { return 0; }",
        "target_arch": "riscv64"
    }
)

# Run ML optimization
response = requests.post(
    "http://localhost:5000/api/llvm/optimize",
    json={
        "code": "int main() { return 0; }",
        "ir_passes": ["mem2reg", "simplifycfg", "instcombine"],
        "target_arch": "riscv64"
    }
)

# Compare with standard
response = requests.post(
    "http://localhost:5000/api/llvm/compare",
    json={
        "code": "int main() { return 0; }",
        "ir_passes": ["mem2reg", "simplifycfg", "instcombine"],
        "target_arch": "riscv64"
    }
)
```

## Key Advantages

1. **Simplified Architecture**: Removed unnecessary complexity from the original backend
2. **RISC-V Focus**: All optimizations specifically target RISC-V hardware
3. **Direct Integration**: Can directly use functions from `generate_training_data_hybrid.py`
4. **Clean API**: Simple JSON input/output format
5. **Comprehensive Metrics**: Execution time, binary size, compilation time
6. **Fair Comparison**: Consistent toolchain for ML and standard optimizations

## Next Steps

1. **Model Integration**: Connect with trained XGBoost model for pass prediction
2. **Pass Sequence Optimization**: Use model to predict optimal pass sequences
3. **Machine Config Support**: Expand machine-level optimization flags
4. **Caching**: Add result caching for frequently tested programs
5. **Batch Processing**: Support multiple programs in single request

## Dependencies

- Python 3.8+
- Flask, Flask-CORS
- LLVM tools (clang, opt, llc)
- RISC-V toolchain (riscv64-linux-gnu-gcc)
- QEMU for RISC-V (qemu-riscv64)

## Notes

- All compilation targets RISC-V architecture per project requirements
- Feature extraction uses unoptimized (-O0) bitcode as baseline
- Execution times measured with QEMU emulation
- Binary sizes include static linking for standalone execution
