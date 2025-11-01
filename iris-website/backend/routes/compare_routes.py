#!/usr/bin/env python3
"""
Comparison Routes - /api/compare endpoints
"""

import time
import json
from pathlib import Path
from flask import request, Blueprint

from services import ComparisonService
from utils import (
    validate_source_file,
    validate_source_code,
    validate_pass_sequence,
    success_response,
    error_response,
    format_comparison_result
)
from utils.logger import get_logger

logger = get_logger(__name__)


def create_compare_routes(comparison_service: ComparisonService) -> Blueprint:
    """
    Create comparison routes.
    
    Args:
        comparison_service: Initialized ComparisonService
    
    Returns:
        Blueprint with comparison routes
    """
    bp = Blueprint('compare', __name__, url_prefix='/api/compare')
    
    @bp.route('', methods=['POST'])
    def compare_optimizations():
        """
        Compare ML-generated optimizations vs standard levels.
        
        Expected JSON input:
        {
            "source_code": "C source code string",
            "ir_passes": ["pass1", "pass2", ...],
            "machine_config": {"flag1": value1, ...}  // optional
        }
        
        Returns:
            Complete comparison results with ML vs -O0/-O1/-O2/-O3
        """
        start_time = time.time()
        
        try:
            data = request.get_json()
            
            if not data:
                return error_response(
                    'No JSON data provided',
                    status_code=400,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Validate inputs
            source_code = data.get('source_code')
            is_valid, error_msg = validate_source_code(source_code)
            if not is_valid:
                return error_response(
                    error_msg,
                    status_code=400,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            ir_passes = data.get('ir_passes', [])
            is_valid, error_msg = validate_pass_sequence(ir_passes)
            if not is_valid:
                return error_response(
                    error_msg,
                    status_code=400,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            machine_config = data.get('machine_config')
            
            logger.info(f"Starting comparison with {len(ir_passes)} IR passes")
            
            # Run comparison
            results = comparison_service.compare_all(
                source_code,
                ir_passes,
                machine_config
            )
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            if 'error' in results and results['error']:
                return error_response(
                    results['error'],
                    status_code=500,
                    processing_time_ms=processing_time_ms
                )
            
            return success_response(results, processing_time_ms=processing_time_ms)
        
        except Exception as e:
            logger.error(f"Comparison failed: {e}", exc_info=True)
            return error_response(
                f'Comparison failed: {str(e)}',
                status_code=500,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @bp.route('/file', methods=['POST'])
    def compare_optimizations_file():
        """
        Compare optimizations from uploaded C file.
        
        Form data:
        - source_file: C source file
        - ir_passes: JSON string of pass list
        - machine_config: JSON string of config (optional)
        
        Returns:
            Complete comparison results
        """
        start_time = time.time()
        
        try:
            # Validate file
            if 'source_file' not in request.files:
                return error_response(
                    'No source file provided',
                    status_code=400,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            file = request.files['source_file']
            is_valid, error_msg = validate_source_file(file)
            if not is_valid:
                return error_response(
                    error_msg,
                    status_code=400,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Read source code
            source_code = file.read().decode('utf-8')
            
            # Parse IR passes
            ir_passes_json = request.form.get('ir_passes')
            if not ir_passes_json:
                return error_response(
                    'ir_passes is required',
                    status_code=400,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            try:
                ir_passes = json.loads(ir_passes_json)
            except json.JSONDecodeError as e:
                return error_response(
                    f'Invalid JSON in ir_passes: {str(e)}',
                    status_code=400,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            is_valid, error_msg = validate_pass_sequence(ir_passes)
            if not is_valid:
                return error_response(
                    error_msg,
                    status_code=400,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Parse machine config (optional)
            machine_config = None
            machine_config_json = request.form.get('machine_config')
            if machine_config_json:
                try:
                    machine_config = json.loads(machine_config_json)
                except json.JSONDecodeError as e:
                    return error_response(
                        f'Invalid JSON in machine_config: {str(e)}',
                        status_code=400,
                        processing_time_ms=(time.time() - start_time) * 1000
                    )
            
            logger.info(f"Starting file comparison: {file.filename}")
            
            # Run comparison
            results = comparison_service.compare_all(
                source_code,
                ir_passes,
                machine_config
            )
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            if 'error' in results and results['error']:
                return error_response(
                    results['error'],
                    status_code=500,
                    processing_time_ms=processing_time_ms
                )
            
            return success_response(results, processing_time_ms=processing_time_ms)
        
        except Exception as e:
            logger.error(f"File comparison failed: {e}", exc_info=True)
            return error_response(
                f'Comparison failed: {str(e)}',
                status_code=500,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @bp.route('/quick', methods=['POST'])
    def quick_compare():
        """
        Quick comparison: ML vs -O3 only (faster than full comparison).
        
        Expected JSON input:
        {
            "source_code": "C source code string",
            "ir_passes": ["pass1", "pass2", ...]
        }
        
        Returns:
            Quick comparison results (ML vs -O3)
        """
        start_time = time.time()
        
        try:
            data = request.get_json()
            
            if not data:
                return error_response(
                    'No JSON data provided',
                    status_code=400,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            source_code = data.get('source_code')
            ir_passes = data.get('ir_passes', [])
            
            # Validate inputs
            is_valid, error_msg = validate_source_code(source_code)
            if not is_valid:
                return error_response(error_msg, status_code=400)
            
            is_valid, error_msg = validate_pass_sequence(ir_passes)
            if not is_valid:
                return error_response(error_msg, status_code=400)
            
            logger.info("Running quick comparison (ML vs -O3)")
            
            # Create temp file and run quick comparison
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as tmp:
                tmp.write(source_code)
                tmp_path = Path(tmp.name)
            
            try:
                results = comparison_service.quick_compare(tmp_path, ir_passes)
                processing_time_ms = (time.time() - start_time) * 1000
                return success_response(results, processing_time_ms=processing_time_ms)
            finally:
                tmp_path.unlink(missing_ok=True)
        
        except Exception as e:
            logger.error(f"Quick comparison failed: {e}", exc_info=True)
            return error_response(
                f'Quick comparison failed: {str(e)}',
                status_code=500,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    return bp
