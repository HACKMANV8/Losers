#!/usr/bin/env python3
"""
Configuration management for IRis Backend API
All paths, settings, and constants centralized here
"""

import os
from pathlib import Path

# ============================================================================
# BASE PATHS
# ============================================================================
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent.parent  # iris-website/backend -> hackman/
TOOLS_DIR = PROJECT_ROOT / "tools"
MODELS_DIR = PROJECT_ROOT / "models"
PREPROCESSING_DIR = PROJECT_ROOT / "preprocessing_output"

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================
class ModelConfig:
    """Configuration for ML models"""
    
    # Transformer Models
    TRANSFORMER_RUNTIME_MODEL = PROJECT_ROOT / "passformer_runtime.pth"
    TRANSFORMER_BINARY_SIZE_MODEL = PROJECT_ROOT / "passformer_binary_size.pth"
    
    # XGBoost Model (if available)
    XGBOOST_MODEL = MODELS_DIR / "combined_model.pkl"
    
    # Training Data
    TRAINING_DATA = TOOLS_DIR / "training_data" / "training_data_flat.json"
    
    # Available models
    AVAILABLE_MODELS = ["transformer", "xgboost"]
    DEFAULT_MODEL = "transformer"

# ============================================================================
# RISC-V COMPILATION CONFIGURATION
# ============================================================================
class CompilationConfig:
    """Configuration for RISC-V compilation and optimization"""
    
    # Target Architecture
    DEFAULT_TARGET_ARCH = "riscv64"
    SUPPORTED_ARCHS = ["riscv64", "riscv32"]
    
    # RISC-V Target Triples
    RISCV64_TRIPLE = "riscv64-unknown-linux-gnu"
    RISCV32_TRIPLE = "riscv32-unknown-linux-gnu"
    
    # Compilation Tools
    CLANG_CMD = "clang"
    OPT_CMD = "opt"
    LLC_CMD = "llc"
    
    # Cross-compilation Tools
    RISCV64_GCC = "riscv64-linux-gnu-gcc"
    RISCV32_GCC = "riscv32-linux-gnu-gcc"
    
    # QEMU Emulation
    QEMU_RISCV64 = "qemu-riscv64"
    QEMU_RISCV32 = "qemu-riscv32"
    USE_QEMU = True  # Required for cross-compiled binaries
    
    # Standard Optimization Levels
    STANDARD_OPT_LEVELS = ["-O0", "-O1", "-O2", "-O3"]
    
    # Timeouts (seconds)
    COMPILE_TIMEOUT = 30
    OPT_TIMEOUT = 60
    EXECUTION_TIMEOUT = 10
    
    # Benchmark Settings
    DEFAULT_NUM_RUNS = 3
    
    # Temporary Directory
    TEMP_DIR = "/tmp/iris_backend"

# ============================================================================
# FEATURE EXTRACTION CONFIGURATION
# ============================================================================
class FeatureConfig:
    """Configuration for LLVM feature extraction"""
    
    # Feature scaler and keys from preprocessing
    FEATURE_SCALER = PREPROCESSING_DIR / "feature_scaler.pkl"
    FEATURE_KEYS = PREPROCESSING_DIR / "feature_keys.json"
    
    # Hardware vocabulary
    HARDWARE_VOCAB = PREPROCESSING_DIR / "hardware_vocab.json"
    JOINT_PASS_VOCAB = PREPROCESSING_DIR / "joint_pass_vocab.json"

# ============================================================================
# API CONFIGURATION
# ============================================================================
class APIConfig:
    """Configuration for Flask API"""
    
    # Server Settings
    HOST = "0.0.0.0"
    PORT = 5001
    DEBUG = True
    
    # CORS Settings
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]
    
    # API Version
    API_VERSION = "1.0.0"
    API_TITLE = "IRis Backend API"
    API_DESCRIPTION = "ML-Guided Compiler Optimization for RISC-V"
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {"c", "cpp", "cc", "cxx"}
    
    # Temporary File Settings
    TEMP_DIR = "/tmp/iris_backend"
    CLEANUP_TEMP_FILES = True

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
class LoggingConfig:
    """Configuration for logging"""
    
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = BACKEND_DIR / "logs" / "iris_backend.log"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

# ============================================================================
# VALIDATION CONFIGURATION
# ============================================================================
class ValidationConfig:
    """Configuration for input validation"""
    
    # Source code validation
    MAX_SOURCE_SIZE = 1024 * 1024  # 1MB
    MIN_SOURCE_SIZE = 10  # 10 bytes
    
    # Pass sequence validation
    MAX_PASS_SEQUENCE_LENGTH = 100
    MIN_PASS_SEQUENCE_LENGTH = 1
    
    # Allowed file extensions
    ALLOWED_SOURCE_EXTENSIONS = [".c", ".cpp", ".cc", ".cxx"]

# ============================================================================
# ERROR MESSAGES
# ============================================================================
class ErrorMessages:
    """Standard error messages"""
    
    # Model Errors
    MODEL_NOT_FOUND = "Model file not found: {}"
    MODEL_LOAD_FAILED = "Failed to load model: {}"
    MODEL_NOT_AVAILABLE = "Model '{}' is not available"
    
    # Compilation Errors
    COMPILATION_FAILED = "Compilation failed: {}"
    OPTIMIZATION_FAILED = "Optimization failed: {}"
    EXECUTION_FAILED = "Execution failed: {}"
    
    # Input Validation Errors
    INVALID_FILE_TYPE = "Invalid file type. Allowed: {}"
    INVALID_MODEL_SELECTION = "Invalid model selection. Available: {}"
    INVALID_TARGET_ARCH = "Invalid target architecture. Supported: {}"
    FILE_TOO_LARGE = "File too large. Maximum size: {} bytes"
    FILE_TOO_SMALL = "File too small. Minimum size: {} bytes"
    NO_FILE_PROVIDED = "No file provided"
    NO_SOURCE_CODE = "No source code provided"
    INVALID_PASS_SEQUENCE = "Invalid pass sequence"
    
    # System Errors
    TOOL_NOT_FOUND = "Required tool not found: {}"
    TIMEOUT_ERROR = "Operation timed out after {} seconds"
    UNEXPECTED_ERROR = "An unexpected error occurred: {}"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def ensure_directories():
    """Create necessary directories if they don't exist"""
    dirs_to_create = [
        APIConfig.TEMP_DIR,
        LoggingConfig.LOG_FILE.parent,
    ]
    
    for directory in dirs_to_create:
        Path(directory).mkdir(parents=True, exist_ok=True)

def get_model_path(model_type: str, metric: str = "runtime") -> Path:
    """
    Get the path to a model file.
    
    Args:
        model_type: 'transformer' or 'xgboost'
        metric: 'runtime' or 'binary_size' (for transformer only)
    
    Returns:
        Path to model file
    """
    if model_type == "transformer":
        if metric == "runtime":
            return ModelConfig.TRANSFORMER_RUNTIME_MODEL
        elif metric == "binary_size":
            return ModelConfig.TRANSFORMER_BINARY_SIZE_MODEL
        else:
            return ModelConfig.TRANSFORMER_RUNTIME_MODEL
    elif model_type == "xgboost":
        return ModelConfig.XGBOOST_MODEL
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def get_target_triple(arch: str) -> str:
    """Get RISC-V target triple for architecture"""
    if arch == "riscv64":
        return CompilationConfig.RISCV64_TRIPLE
    elif arch == "riscv32":
        return CompilationConfig.RISCV32_TRIPLE
    else:
        raise ValueError(f"Unsupported architecture: {arch}")

def get_gcc_command(arch: str) -> str:
    """Get GCC cross-compiler command for architecture"""
    if arch == "riscv64":
        return CompilationConfig.RISCV64_GCC
    elif arch == "riscv32":
        return CompilationConfig.RISCV32_GCC
    else:
        raise ValueError(f"Unsupported architecture: {arch}")

def get_qemu_command(arch: str) -> str:
    """Get QEMU command for architecture"""
    if arch == "riscv64":
        return CompilationConfig.QEMU_RISCV64
    elif arch == "riscv32":
        return CompilationConfig.QEMU_RISCV32
    else:
        raise ValueError(f"Unsupported architecture: {arch}")

# Initialize directories on module import
ensure_directories()
