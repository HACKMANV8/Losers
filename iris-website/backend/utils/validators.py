#!/usr/bin/env python3
"""
Input validation utilities for IRis Backend
"""

from pathlib import Path
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage

from config import (
    ValidationConfig,
    ModelConfig,
    CompilationConfig,
    ErrorMessages,
    APIConfig
)


def validate_source_file(file: Optional[FileStorage]) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded source file.
    
    Args:
        file: Uploaded file object from Flask request
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file:
        return False, ErrorMessages.NO_FILE_PROVIDED
    
    if file.filename == '':
        return False, ErrorMessages.NO_FILE_PROVIDED
    
    # Check file extension
    if '.' not in file.filename:
        return False, ErrorMessages.INVALID_FILE_TYPE.format(
            ', '.join(APIConfig.ALLOWED_EXTENSIONS)
        )
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in APIConfig.ALLOWED_EXTENSIONS:
        return False, ErrorMessages.INVALID_FILE_TYPE.format(
            ', '.join(APIConfig.ALLOWED_EXTENSIONS)
        )
    
    # Check file size (if possible)
    try:
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if size > ValidationConfig.MAX_SOURCE_SIZE:
            return False, ErrorMessages.FILE_TOO_LARGE.format(
                ValidationConfig.MAX_SOURCE_SIZE
            )
        
        if size < ValidationConfig.MIN_SOURCE_SIZE:
            return False, ErrorMessages.FILE_TOO_SMALL.format(
                ValidationConfig.MIN_SOURCE_SIZE
            )
    except Exception:
        # If we can't check size, continue anyway
        pass
    
    return True, None


def validate_source_code(source_code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate source code string.
    
    Args:
        source_code: C/C++ source code as string
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not source_code:
        return False, ErrorMessages.NO_SOURCE_CODE
    
    if len(source_code.encode('utf-8')) > ValidationConfig.MAX_SOURCE_SIZE:
        return False, ErrorMessages.FILE_TOO_LARGE.format(
            ValidationConfig.MAX_SOURCE_SIZE
        )
    
    if len(source_code.strip()) < ValidationConfig.MIN_SOURCE_SIZE:
        return False, ErrorMessages.FILE_TOO_SMALL.format(
            ValidationConfig.MIN_SOURCE_SIZE
        )
    
    return True, None


def validate_model_selection(model: str) -> Tuple[bool, Optional[str]]:
    """
    Validate model selection.
    
    Args:
        model: Model name (e.g., 'transformer', 'xgboost')
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not model:
        return False, ErrorMessages.INVALID_MODEL_SELECTION.format(
            ', '.join(ModelConfig.AVAILABLE_MODELS)
        )
    
    if model not in ModelConfig.AVAILABLE_MODELS:
        return False, ErrorMessages.INVALID_MODEL_SELECTION.format(
            ', '.join(ModelConfig.AVAILABLE_MODELS)
        )
    
    return True, None


def validate_target_arch(arch: str) -> Tuple[bool, Optional[str]]:
    """
    Validate target architecture.
    
    Args:
        arch: Target architecture (e.g., 'riscv64', 'riscv32')
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not arch:
        return False, ErrorMessages.INVALID_TARGET_ARCH.format(
            ', '.join(CompilationConfig.SUPPORTED_ARCHS)
        )
    
    if arch not in CompilationConfig.SUPPORTED_ARCHS:
        return False, ErrorMessages.INVALID_TARGET_ARCH.format(
            ', '.join(CompilationConfig.SUPPORTED_ARCHS)
        )
    
    return True, None


def validate_pass_sequence(passes: list) -> Tuple[bool, Optional[str]]:
    """
    Validate LLVM pass sequence.
    
    Args:
        passes: List of pass names
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not passes:
        return False, ErrorMessages.INVALID_PASS_SEQUENCE
    
    if not isinstance(passes, list):
        return False, ErrorMessages.INVALID_PASS_SEQUENCE
    
    if len(passes) > ValidationConfig.MAX_PASS_SEQUENCE_LENGTH:
        return False, f"Pass sequence too long. Maximum: {ValidationConfig.MAX_PASS_SEQUENCE_LENGTH}"
    
    if len(passes) < ValidationConfig.MIN_PASS_SEQUENCE_LENGTH:
        return False, f"Pass sequence too short. Minimum: {ValidationConfig.MIN_PASS_SEQUENCE_LENGTH}"
    
    # Check that all passes are strings
    if not all(isinstance(p, str) for p in passes):
        return False, ErrorMessages.INVALID_PASS_SEQUENCE
    
    return True, None


def validate_optimization_level(opt_level: str) -> Tuple[bool, Optional[str]]:
    """
    Validate optimization level.
    
    Args:
        opt_level: Optimization level (e.g., '-O0', '-O1', '-O2', '-O3')
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if opt_level not in CompilationConfig.STANDARD_OPT_LEVELS:
        return False, f"Invalid optimization level. Allowed: {', '.join(CompilationConfig.STANDARD_OPT_LEVELS)}"
    
    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove path components, keep only basename
    safe_name = Path(filename).name
    
    # Remove any non-alphanumeric characters except . _ -
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '._-')
    
    return safe_name
