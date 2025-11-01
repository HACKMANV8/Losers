#!/usr/bin/env python3
"""
Utility Routes - Health checks and system status endpoints
"""

import time
import tempfile
from pathlib import Path
from flask import request, Blueprint

from config import APIConfig, CompilationConfig
from services import ModelService, FeatureService, CompilationService
from utils import (
    validate_source_file,
    success_response,
    error_response,
    format_system_status
)
from utils.logger import get_logger

logger = get_logger(__name__)


def create_utility_routes(
    model_service: ModelService,
    feature_service: FeatureService,
    compilation_service: CompilationService
) -> Blueprint:
    """
    Create utility routes.
    
    Args:
        model_service: Initialized ModelService
        feature_service: Initialized FeatureService
        compilation_service: Initialized CompilationService
    
    Returns:
        Blueprint with utility routes
    """
    bp = Blueprint('utility', __name__, url_prefix='/api')
    
    @bp.route('/health', methods=['GET'])
    def health_check():
        """
        Simple health check endpoint.
        
        Returns:
            JSON indicating service is running
        """
        return success_response({
            'status': 'healthy',
            'service': 'IRis Backend API',
            'version': APIConfig.API_VERSION
        })
    
    @bp.route('/status', methods=['GET'])
    def detailed_status():
        """
        Detailed status check with models and tools availability.
        
        Returns:
            JSON with comprehensive status information
        """
        start_time = time.time()
        
        try:
            # Check models
            models_loaded = {
                'transformer': model_service.is_model_available('transformer'),
                'xgboost': model_service.is_model_available('xgboost')
            }
            
            # Check tools
            import shutil
            tools_available = {
                'clang': shutil.which('clang') is not None,
                'opt': shutil.which('opt') is not None,
                'llc': shutil.which('llc') is not None,
                'riscv64-gcc': shutil.which('riscv64-linux-gnu-gcc') is not None,
                'qemu-riscv64': shutil.which('qemu-riscv64') is not None
            }
            
            # System info
            system_info = {
                'target_architecture': CompilationConfig.DEFAULT_TARGET_ARCH,
                'temp_directory': str(APIConfig.TEMP_DIR),
                'api_version': APIConfig.API_VERSION
            }
            
            status_data = format_system_status(
                models_loaded,
                tools_available,
                system_info
            )
            
            processing_time_ms = (time.time() - start_time) * 1000
            return success_response(status_data, processing_time_ms=processing_time_ms)
        
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return error_response(
                f"Status check failed: {str(e)}",
                status_code=500,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @bp.route('/info', methods=['GET'])
    def api_info():
        """
        Get API information and available endpoints.
        
        Returns:
            JSON with API metadata
        """
        data = {
            'api_name': APIConfig.API_TITLE,
            'version': APIConfig.API_VERSION,
            'description': APIConfig.API_DESCRIPTION,
            'endpoints': {
                'optimization': [
                    'POST /api/optimize - Optimize code with ML models'
                ],
                'comparison': [
                    'POST /api/compare - Compare ML vs standard optimizations',
                    'POST /api/compare/file - Compare using uploaded file',
                    'POST /api/compare/quick - Quick comparison (ML vs -O3)'
                ],
                'analytics': [
                    'GET /api/analytics/models - Model information',
                    'GET /api/analytics/features - Feature extraction info',
                    'GET /api/analytics/passes - LLVM passes information',
                    'GET /api/analytics/system - System capabilities'
                ],
                'utility': [
                    'GET /api/health - Health check',
                    'GET /api/status - Detailed status',
                    'GET /api/info - API information',
                    'POST /api/validate/source - Validate source code'
                ]
            },
            'supported_models': ['transformer', 'xgboost'],
            'target_architecture': 'RISC-V (riscv64)',
            'optimization_levels': ['-O0', '-O1', '-O2', '-O3']
        }
        
        return success_response(data)
    
    @bp.route('/validate/source', methods=['POST'])
    def validate_source():
        """
        Validate C source code without running full optimization.
        Just checks if code can be compiled to LLVM IR.
        
        Expected form data:
        - source_file: C/C++ source file
        
        Returns:
            JSON with validation result
        """
        start_time = time.time()
        
        try:
            if 'source_file' not in request.files:
                return error_response(
                    "No source file provided",
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
            
            # Save to temp file and try to compile
            temp_file_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix='.c',
                    dir=Path(APIConfig.TEMP_DIR).absolute() if Path(APIConfig.TEMP_DIR).exists() else None
                ) as temp_file:
                    file.save(temp_file.name)
                    temp_file_path = Path(temp_file.name)
                
                logger.info(f"Validating file: {file.filename}")
                
                # Try to compile to bitcode
                success, bc_file, error_msg = compilation_service.compile_to_bitcode(
                    temp_file_path,
                    optimization="-O0"
                )
                
                # Cleanup bitcode if created
                if bc_file and bc_file.exists():
                    bc_file.unlink()
                
                processing_time_ms = (time.time() - start_time) * 1000
                
                if success:
                    return success_response(
                        {
                            'valid': True,
                            'message': 'Source code is valid and can be compiled',
                            'filename': file.filename
                        },
                        processing_time_ms=processing_time_ms
                    )
                else:
                    return success_response(
                        {
                            'valid': False,
                            'message': 'Source code has compilation errors',
                            'error': error_msg,
                            'filename': file.filename
                        },
                        processing_time_ms=processing_time_ms
                    )
            
            finally:
                # Cleanup temp file
                if temp_file_path and temp_file_path.exists():
                    temp_file_path.unlink()
        
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return error_response(
                f"Validation failed: {str(e)}",
                status_code=500,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    return bp
