#!/usr/bin/env python3
"""
Simplified LLVM API Routes - Core functionality for ML optimization
"""

from flask import Blueprint, request, jsonify
from pathlib import Path
import tempfile
from typing import Dict, List, Any

from services.llvm_optimization_service import LLVMOptimizationService
from utils.logger import get_logger

logger = get_logger(__name__)

llvm_api = Blueprint('llvm_api', __name__, url_prefix='/api/llvm')

# Initialize service (singleton pattern)
_service = None

def get_service(target_arch: str = "riscv64") -> LLVMOptimizationService:
    """Get or create the LLVM optimization service."""
    global _service
    if _service is None or _service.target_arch != target_arch:
        _service = LLVMOptimizationService(target_arch=target_arch)
    return _service


@llvm_api.route('/features', methods=['POST'])
def extract_features():
    """
    Extract features from C source code.
    
    Request JSON:
    {
        "code": "C source code string",
        "target_arch": "riscv64" (optional)
    }
    
    Response JSON:
    {
        "success": true/false,
        "features": {...},
        "error": "error message if failed"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400
        
        c_code = data['code']
        target_arch = data.get('target_arch', 'riscv64')
        
        service = get_service(target_arch)
        success, features, error = service.extract_features_from_c(c_code)
        
        if success:
            return jsonify({
                'success': True,
                'features': features,
                'feature_count': len(features) if features else 0
            })
        else:
            return jsonify({
                'success': False,
                'error': error
            }), 500
            
    except Exception as e:
        logger.error(f"Feature extraction error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@llvm_api.route('/optimize', methods=['POST'])
def run_optimization():
    """
    Run ML-generated optimization passes on C code.
    
    Request JSON:
    {
        "code": "C source code string",
        "ir_passes": ["pass1", "pass2", ...],
        "machine_config": {...} (optional),
        "target_arch": "riscv64" (optional)
    }
    
    Response JSON:
    {
        "success": true/false,
        "metrics": {
            "execution_time_avg": float,
            "binary_size": int,
            ...
        },
        "error": "error message if failed"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400
        
        if 'ir_passes' not in data:
            return jsonify({
                'success': False,
                'error': 'No IR passes provided'
            }), 400
        
        c_code = data['code']
        ir_passes = data['ir_passes']
        machine_config = data.get('machine_config', None)
        target_arch = data.get('target_arch', 'riscv64')
        
        # Validate passes
        if not isinstance(ir_passes, list):
            return jsonify({
                'success': False,
                'error': 'IR passes must be a list'
            }), 400
        
        service = get_service(target_arch)
        success, metrics, error = service.run_ml_passes(c_code, ir_passes, machine_config)
        
        if success:
            return jsonify({
                'success': True,
                'metrics': metrics
            })
        else:
            return jsonify({
                'success': False,
                'error': error
            }), 500
            
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@llvm_api.route('/standard', methods=['POST'])
def run_standard_optimizations():
    """
    Run standard optimization levels on C code.
    
    Request JSON:
    {
        "code": "C source code string",
        "opt_levels": ["-O0", "-O1", "-O2", "-O3"] (optional),
        "target_arch": "riscv64" (optional)
    }
    
    Response JSON:
    {
        "success": true,
        "results": {
            "-O0": {...},
            "-O1": {...},
            ...
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400
        
        c_code = data['code']
        opt_levels = data.get('opt_levels', ["-O0", "-O1", "-O2", "-O3"])
        target_arch = data.get('target_arch', 'riscv64')
        
        service = get_service(target_arch)
        results = service.run_standard_optimizations(c_code, opt_levels)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Standard optimization error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@llvm_api.route('/compare', methods=['POST'])
def compare_optimizations():
    """
    Compare ML optimization with standard optimizations.
    
    Request JSON:
    {
        "code": "C source code string",
        "ir_passes": ["pass1", "pass2", ...],
        "machine_config": {...} (optional),
        "target_arch": "riscv64" (optional)
    }
    
    Response JSON:
    {
        "success": true,
        "features": {...},
        "ml_optimization": {...},
        "standard_optimizations": {
            "-O0": {...},
            "-O1": {...},
            ...
        },
        "comparison": {
            "-O0": {
                "speedup": float,
                "size_reduction": float,
                "ml_faster": bool,
                "ml_smaller": bool
            },
            ...
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400
        
        if 'ir_passes' not in data:
            return jsonify({
                'success': False,
                'error': 'No IR passes provided'
            }), 400
        
        c_code = data['code']
        ir_passes = data['ir_passes']
        machine_config = data.get('machine_config', None)
        target_arch = data.get('target_arch', 'riscv64')
        
        service = get_service(target_arch)
        results = service.compare_with_standard(c_code, ir_passes, machine_config)
        
        return jsonify({
            'success': True,
            **results
        })
        
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@llvm_api.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Response JSON:
    {
        "status": "healthy",
        "service": "llvm_optimization",
        "target_arch": "riscv64"
    }
    """
    try:
        service = get_service()
        return jsonify({
            'status': 'healthy',
            'service': 'llvm_optimization',
            'target_arch': service.target_arch
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
