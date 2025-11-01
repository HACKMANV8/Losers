#!/usr/bin/env python3
"""
IRis Backend API - Main Application
ML-Guided Compiler Optimization for RISC-V Architecture
"""

import sys
import os
from pathlib import Path
from flask import Flask
from flask_cors import CORS

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import APIConfig, CompilationConfig
from services import ModelService, FeatureService, CompilationService, ComparisonService
from routes import (
    create_optimize_routes,
    create_compare_routes,
    create_analytics_routes,
    create_utility_routes
)
from utils.logger import setup_logger, get_logger

# Setup logging
setup_logger()
logger = get_logger(__name__)


def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Configured Flask app instance
    """
    logger.info("="*60)
    logger.info("IRis Backend API Starting...")
    logger.info("="*60)
    
    # Initialize Flask app
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = APIConfig.MAX_CONTENT_LENGTH
    
    # Enable CORS
    CORS(app, origins=APIConfig.CORS_ORIGINS)
    logger.info("✓ CORS enabled")
    
    # Initialize services
    logger.info("Initializing services...")
    
    try:
        model_service = ModelService()
        logger.info("✓ ModelService initialized")
        
        feature_service = FeatureService(target_arch=CompilationConfig.DEFAULT_TARGET_ARCH)
        logger.info("✓ FeatureService initialized")
        
        compilation_service = CompilationService(target_arch=CompilationConfig.DEFAULT_TARGET_ARCH)
        logger.info("✓ CompilationService initialized")
        
        comparison_service = ComparisonService(target_arch=CompilationConfig.DEFAULT_TARGET_ARCH)
        logger.info("✓ ComparisonService initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    # Register routes
    logger.info("Registering routes...")
    
    try:
        # Optimization routes
        optimize_bp = create_optimize_routes(model_service, feature_service)
        app.register_blueprint(optimize_bp)
        logger.info("✓ Optimization routes registered")
        
        # Comparison routes
        compare_bp = create_compare_routes(comparison_service)
        app.register_blueprint(compare_bp)
        logger.info("✓ Comparison routes registered")
        
        # Analytics routes
        analytics_bp = create_analytics_routes(model_service, feature_service)
        app.register_blueprint(analytics_bp)
        logger.info("✓ Analytics routes registered")
        
        # Utility routes
        utility_bp = create_utility_routes(model_service, feature_service, compilation_service)
        app.register_blueprint(utility_bp)
        logger.info("✓ Utility routes registered")
        
    except Exception as e:
        logger.error(f"Failed to register routes: {e}")
        raise
    
    # Home route
    @app.route('/')
    def home():
        """API root endpoint"""
        return {
            "service": APIConfig.API_TITLE,
            "version": APIConfig.API_VERSION,
            "description": APIConfig.API_DESCRIPTION,
            "status": "running",
            "endpoints": {
                "info": "/api/info",
                "health": "/api/health",
                "status": "/api/status"
            }
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return {
            "success": False,
            "error": "Endpoint not found",
            "message": "The requested endpoint does not exist. See /api/info for available endpoints."
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal server error: {error}")
        return {
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }, 500
    
    logger.info("="*60)
    logger.info("IRis Backend API Ready!")
    logger.info(f"Target Architecture: {CompilationConfig.DEFAULT_TARGET_ARCH}")
    logger.info(f"Available Models: {model_service.get_available_models()}")
    logger.info("="*60)
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    logger.info(f"Starting server on {APIConfig.HOST}:{APIConfig.PORT}")
    logger.info(f"Debug mode: {APIConfig.DEBUG}")
    
    app.run(
        host=APIConfig.HOST,
        port=APIConfig.PORT,
        debug=APIConfig.DEBUG
    )
