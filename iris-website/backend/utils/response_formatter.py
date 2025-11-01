#!/usr/bin/env python3
"""
Response formatting utilities for IRis Backend
Provides consistent API response structure
"""

from typing import Any, Dict, Optional
from datetime import datetime
from flask import jsonify

from config import APIConfig


def _get_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()


def success_response(
    data: Any,
    processing_time_ms: Optional[float] = None,
    message: Optional[str] = None
) -> tuple:
    """
    Create a standardized success response.
    
    Args:
        data: Response data (dict, list, or any JSON-serializable object)
        processing_time_ms: Processing time in milliseconds
        message: Optional success message
    
    Returns:
        Tuple of (jsonified response, status_code)
    """
    response = {
        "success": True,
        "data": data,
        "error": None,
        "metadata": {
            "timestamp": _get_timestamp(),
            "version": APIConfig.API_VERSION,
        }
    }
    
    if processing_time_ms is not None:
        response["metadata"]["processing_time_ms"] = round(processing_time_ms, 2)
    
    if message:
        response["message"] = message
    
    return jsonify(response), 200


def error_response(
    error: str,
    status_code: int = 500,
    processing_time_ms: Optional[float] = None,
    details: Optional[Dict] = None
) -> tuple:
    """
    Create a standardized error response.
    
    Args:
        error: Error message
        status_code: HTTP status code
        processing_time_ms: Processing time in milliseconds
        details: Additional error details
    
    Returns:
        Tuple of (jsonified response, status_code)
    """
    response = {
        "success": False,
        "data": None,
        "error": error,
        "metadata": {
            "timestamp": _get_timestamp(),
            "version": APIConfig.API_VERSION,
        }
    }
    
    if processing_time_ms is not None:
        response["metadata"]["processing_time_ms"] = round(processing_time_ms, 2)
    
    if details:
        response["error_details"] = details
    
    return jsonify(response), status_code


def format_optimization_result(
    success: bool,
    model_used: str,
    predicted_passes: Optional[list],
    features: Optional[dict],
    processing_time_ms: float,
    error_msg: Optional[str] = None
) -> dict:
    """
    Format optimization result in standardized format.
    
    Args:
        success: Whether optimization succeeded
        model_used: Model name used for prediction
        predicted_passes: List of predicted passes
        features: Extracted features dictionary
        processing_time_ms: Processing time
        error_msg: Error message if failed
    
    Returns:
        Formatted result dictionary
    """
    result = {
        "success": success,
        "model_used": model_used,
        "predicted_passes": predicted_passes,
        "features": features,
        "processing_time_ms": round(processing_time_ms, 2),
        "error": error_msg
    }
    
    # Add metadata about prediction
    if predicted_passes:
        result["metadata"] = {
            "num_passes": len(predicted_passes),
            "pass_sequence_string": " ".join(predicted_passes)
        }
    
    return result


def format_comparison_result(
    ml_result: Dict,
    standard_results: Dict,
    comparison_summary: Dict,
    target_arch: str,
    total_time: float
) -> dict:
    """
    Format comparison result in standardized format.
    
    Args:
        ml_result: ML optimization result
        standard_results: Standard optimization results dict
        comparison_summary: Comparison summary dict
        target_arch: Target architecture
        total_time: Total processing time
    
    Returns:
        Formatted comparison result
    """
    return {
        "target_arch": target_arch,
        "ml_optimization": ml_result,
        "standard_optimizations": standard_results,
        "comparison_summary": comparison_summary,
        "total_time": round(total_time, 2),
        "metadata": {
            "timestamp": _get_timestamp(),
            "num_comparisons": len(standard_results)
        }
    }


def format_model_info(
    name: str,
    type: str,
    status: str,
    path: Optional[str] = None,
    capabilities: Optional[list] = None,
    details: Optional[dict] = None
) -> dict:
    """
    Format model information.
    
    Args:
        name: Model name
        type: Model type
        status: Model status ('loaded', 'not_found', 'error')
        path: Path to model file
        capabilities: List of capabilities
        details: Additional details
    
    Returns:
        Formatted model info
    """
    info = {
        "name": name,
        "type": type,
        "status": status,
        "path": path,
        "capabilities": capabilities or []
    }
    
    if details:
        info["details"] = details
    
    return info


def format_feature_info(
    features: dict,
    feature_count: int,
    extraction_time_ms: float
) -> dict:
    """
    Format feature extraction information.
    
    Args:
        features: Extracted features dict
        feature_count: Number of features
        extraction_time_ms: Extraction time
    
    Returns:
        Formatted feature info
    """
    return {
        "features": features,
        "metadata": {
            "feature_count": feature_count,
            "extraction_time_ms": round(extraction_time_ms, 2),
            "timestamp": _get_timestamp()
        }
    }


def format_compilation_result(
    success: bool,
    opt_level: Optional[str] = None,
    compile_time: Optional[float] = None,
    execution_time_avg: Optional[float] = None,
    binary_size: Optional[int] = None,
    error_msg: Optional[str] = None,
    additional_metrics: Optional[dict] = None
) -> dict:
    """
    Format compilation result.
    
    Args:
        success: Whether compilation succeeded
        opt_level: Optimization level used
        compile_time: Compilation time in seconds
        execution_time_avg: Average execution time
        binary_size: Binary size in bytes
        error_msg: Error message if failed
        additional_metrics: Additional metrics
    
    Returns:
        Formatted compilation result
    """
    result = {
        "success": success,
        "opt_level": opt_level,
        "compile_time": compile_time,
        "execution_time_avg": execution_time_avg,
        "binary_size": binary_size,
        "error": error_msg
    }
    
    if additional_metrics:
        result["additional_metrics"] = additional_metrics
    
    return result


def format_system_status(
    models_loaded: dict,
    tools_available: dict,
    system_info: dict
) -> dict:
    """
    Format system status information.
    
    Args:
        models_loaded: Dict of loaded models
        tools_available: Dict of available tools
        system_info: System information
    
    Returns:
        Formatted system status
    """
    return {
        "status": "healthy" if all(models_loaded.values()) else "degraded",
        "models": models_loaded,
        "tools": tools_available,
        "system": system_info,
        "timestamp": _get_timestamp()
    }
