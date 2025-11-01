#!/usr/bin/env python3
"""
Optimization Routes - /api/optimize endpoints
"""

import time
import tempfile
from pathlib import Path
from flask import request, Blueprint

from config import APIConfig
from services import ModelService, FeatureService
from utils import (
    validate_source_file,
    validate_model_selection,
    success_response,
    error_response,
    format_optimization_result
)
from utils.logger import get_logger

logger = get_logger(__name__)


def create_optimize_routes(model_service: ModelService, feature_service: FeatureService) -> Blueprint:
    """
    Create optimization routes.
    
    Args:
        model_service: Initialized ModelService
        feature_service: Initialized FeatureService
    
    Returns:
        Blueprint with optimization routes
    """
    bp = Blueprint('optimize', __name__, url_prefix='/api')
    
    @bp.route('/optimize', methods=['POST'])
    def optimize():
        """
        Optimize C/C++ code using ML models.
        
        Expected form data:
        - source_file: C/C++ source file (required)
        - model_selection: 'transformer' or 'xgboost' (required)
        
        Returns:
            JSON response with predicted passes and features
        """
        start_time = time.time()
        
        try:
            # 1. Validate file upload
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
            
            # 2. Validate model selection
            model_selection = request.form.get('model_selection')
            is_valid, error_msg = validate_model_selection(model_selection)
            if not is_valid:
                return error_response(
                    error_msg,
                    status_code=400,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # 3. Check if model is available
            if not model_service.is_model_available(model_selection):
                return error_response(
                    f"Model '{model_selection}' is not available or failed to load",
                    status_code=503,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # 4. Save uploaded file temporarily
            temp_file_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix='.c',
                    dir=Path(APIConfig.TEMP_DIR).absolute() if Path(APIConfig.TEMP_DIR).exists() else None
                ) as temp_file:
                    file.save(temp_file.name)
                    temp_file_path = Path(temp_file.name)
                
                logger.info(f"Processing file: {file.filename} ({temp_file_path})")
                
                # 5. Extract features
                success, features, error_msg, extraction_time = feature_service.extract_from_file(
                    temp_file_path
                )
                
                if not success:
                    return error_response(
                        f"Feature extraction failed: {error_msg}",
                        status_code=500,
                        processing_time_ms=(time.time() - start_time) * 1000
                    )
                
                logger.info(f"Extracted {len(features)} features in {extraction_time:.2f}ms")
                
                # 6. Model inference
                success, predicted_passes, error_msg = model_service.predict(
                    features,
                    model_type=model_selection
                )
                
                if not success:
                    return error_response(
                        error_msg,
                        status_code=500,
                        processing_time_ms=(time.time() - start_time) * 1000
                    )
                
                logger.info(f"Predicted {len(predicted_passes)} passes using {model_selection}")
                
                # 7. Format and return success response
                processing_time_ms = (time.time() - start_time) * 1000
                
                result = format_optimization_result(
                    success=True,
                    model_used=model_selection,
                    predicted_passes=predicted_passes,
                    features=features,
                    processing_time_ms=processing_time_ms,
                    error_msg=None
                )
                
                return success_response(result, processing_time_ms=processing_time_ms)
                
            finally:
                # Cleanup temporary file
                if temp_file_path and temp_file_path.exists():
                    temp_file_path.unlink()
                    logger.debug(f"Cleaned up temp file: {temp_file_path}")
        
        except Exception as e:
            logger.error(f"Unexpected error in /api/optimize: {e}", exc_info=True)
            return error_response(
                f"An unexpected server error occurred: {str(e)}",
                status_code=500,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    return bp
