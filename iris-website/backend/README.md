# IRis Backend API

ML-Guided Compiler Optimization for RISC-V Architecture

## Overview

IRis Backend is a Flask-based REST API that provides machine learning-guided compiler optimization for RISC-V programs. It uses Transformer and XGBoost models to predict optimal LLVM pass sequences and compares them against standard optimization levels (-O0, -O1, -O2, -O3).

## Architecture

```
backend/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── compare_api.py             # Legacy comparison API (can be removed)
├── routes/                     # API route handlers
│   ├── optimize_routes.py     # /api/optimize endpoints
│   ├── compare_routes.py      # /api/compare/* endpoints
│   ├── analytics_routes.py    # /api/analytics/* endpoints
│   └── utility_routes.py      # /api/health, /api/status, etc.
├── services/                   # Business logic layer
│   ├── model_service.py       # ML model management
│   ├── feature_service.py     # Feature extraction
│   ├── compilation_service.py # Compilation & optimization
│   └── comparison_service.py  # Comparison logic
└── utils/                      # Utility modules
    ├── validators.py          # Input validation
    ├── response_formatter.py  # Consistent API responses
    └── logger.py              # Logging configuration
```

## Features

### 1. Optimization Endpoints
- **POST /api/optimize** - Upload C/C++ code and get ML-predicted pass sequences

### 2. Comparison Endpoints
- **POST /api/compare** - Compare ML vs standard optimization levels
- **POST /api/compare/file** - Compare using uploaded file
- **POST /api/compare/quick** - Quick comparison (ML vs -O3)

### 3. Analytics Endpoints
- **GET /api/analytics/models** - Model information and status
- **GET /api/analytics/features** - Feature extraction capabilities
- **GET /api/analytics/passes** - Available LLVM passes catalog
- **GET /api/analytics/system** - System capabilities and tool versions

### 4. Utility Endpoints
- **GET /api/health** - Simple health check
- **GET /api/status** - Detailed system status
- **GET /api/info** - API information and available endpoints
- **POST /api/validate/source** - Validate C source code

## Prerequisites

### System Requirements
- Python 3.8+
- LLVM/Clang toolchain
- RISC-V cross-compilation toolchain
- QEMU for RISC-V emulation

### Required Tools
```bash
# Check if tools are installed
clang --version
opt --version
llc --version
riscv64-linux-gnu-gcc --version
qemu-riscv64 --version
```

### Installation on Ubuntu/Debian
```bash
# Install LLVM tools
sudo apt-get install clang llvm

# Install RISC-V toolchain
sudo apt-get install gcc-riscv64-linux-gnu

# Install QEMU
sudo apt-get install qemu-user
```

## Setup

### 1. Install Python Dependencies
```bash
cd iris-website/backend
pip install -r requirements.txt
```

### 2. Ensure Models Are Available
The backend expects these model files in the project root:
- `passformer_binary_size.pth` or `passformer_runtime.pth` (Transformer model)
- `models/combined_model.pkl` (XGBoost model - optional)

### 3. Configure Environment
Edit `config.py` to adjust:
- Model paths
- Target architecture (default: riscv64)
- Compilation timeouts
- API settings

## Running the Backend

### Development Mode
```bash
python app.py
```

The API will start on `http://localhost:5001`

### Production Mode
For production, use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:create_app()
```

## API Usage Examples

### 1. Optimize Code
```bash
curl -X POST http://localhost:5001/api/optimize \
  -F "source_file=@program.c" \
  -F "model_selection=transformer"
```

Response:
```json
{
  "success": true,
  "data": {
    "model_used": "transformer",
    "predicted_passes": ["mem2reg", "instcombine", "gvn", ...],
    "features": { "total_instructions": 138, ... },
    "processing_time_ms": 523.45
  }
}
```

### 2. Compare Optimizations
```bash
curl -X POST http://localhost:5001/api/compare \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "#include <stdio.h>\nint main() { return 0; }",
    "ir_passes": ["mem2reg", "instcombine", "gvn"]
  }'
```

### 3. Get System Status
```bash
curl http://localhost:5001/api/status
```

### 4. Get Model Information
```bash
curl http://localhost:5001/api/analytics/models
```

## Configuration

Key configuration options in `config.py`:

### Model Configuration
```python
ModelConfig.TRANSFORMER_RUNTIME_MODEL  # Path to Transformer model
ModelConfig.XGBOOST_MODEL              # Path to XGBoost model
```

### Compilation Configuration
```python
CompilationConfig.DEFAULT_TARGET_ARCH  # riscv64 or riscv32
CompilationConfig.COMPILE_TIMEOUT      # Compilation timeout (seconds)
CompilationConfig.EXECUTION_TIMEOUT    # Execution timeout (seconds)
```

### API Configuration
```python
APIConfig.HOST                         # Server host
APIConfig.PORT                         # Server port (default: 5001)
APIConfig.CORS_ORIGINS                 # Allowed CORS origins
```

## Error Handling

All endpoints return consistent error responses:
```json
{
  "success": false,
  "data": null,
  "error": "Error message here",
  "metadata": {
    "timestamp": "2025-11-01T03:47:23",
    "version": "1.0.0",
    "processing_time_ms": 123.45
  }
}
```

## Logging

Logs are stored in `backend/logs/iris_backend.log` with rotation.

To change log level, edit `LoggingConfig.LOG_LEVEL` in `config.py`:
- `DEBUG` - Detailed information
- `INFO` - General information (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

## Testing

### Health Check
```bash
curl http://localhost:5001/api/health
```

### Validate Source Code
```bash
curl -X POST http://localhost:5001/api/validate/source \
  -F "source_file=@test.c"
```

## Troubleshooting

### Model Not Loading
- Check if model files exist at configured paths
- Verify PyTorch installation: `python -c "import torch; print(torch.__version__)"`

### Compilation Errors
- Verify RISC-V toolchain: `riscv64-linux-gnu-gcc --version`
- Check QEMU installation: `qemu-riscv64 --version`
- Ensure clang supports RISC-V target: `clang --print-targets | grep riscv`

### CORS Issues
- Check `APIConfig.CORS_ORIGINS` in `config.py`
- Ensure frontend URL is in allowed origins

## Development

### Adding New Endpoints
1. Create route function in appropriate route file
2. Add validation using utilities from `utils/validators.py`
3. Use `success_response()` or `error_response()` for consistency
4. Add logging for debugging

### Adding New Services
1. Create service class in `services/`
2. Initialize in `app.py` `create_app()` function
3. Pass to route creation functions as needed

## License

Part of the IRis project - ML-Guided Compiler Optimization System

## Contact

For issues or questions, please refer to the main project documentation.
