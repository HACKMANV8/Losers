#!/usr/bin/env python3
"""
Analytics Routes - /api/analytics endpoints
"""

import time
from flask import Blueprint

from services import ModelService, FeatureService
from utils import success_response, error_response
from utils.logger import get_logger

logger = get_logger(__name__)


def create_analytics_routes(model_service: ModelService, feature_service: FeatureService) -> Blueprint:
    """
    Create analytics routes.
    
    Args:
        model_service: Initialized ModelService
        feature_service: Initialized FeatureService
    
    Returns:
        Blueprint with analytics routes
    """
    bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
    
    @bp.route('/models', methods=['GET'])
    def get_models_info():
        """
        Get information about loaded ML models.
        
        Returns:
            JSON with model information
        """
        start_time = time.time()
        
        try:
            model_info = model_service.get_model_info()
            available_models = model_service.get_available_models()
            
            data = {
                'models': model_info,
                'available': available_models,
                'total_available': len(available_models)
            }
            
            processing_time_ms = (time.time() - start_time) * 1000
            return success_response(data, processing_time_ms=processing_time_ms)
        
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return error_response(
                f"Failed to retrieve model information: {str(e)}",
                status_code=500,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @bp.route('/features', methods=['GET'])
    def get_feature_info():
        """
        Get information about feature extraction capabilities.
        
        Returns:
            JSON with feature extraction information
        """
        start_time = time.time()
        
        try:
            # Get sample feature names from model service
            if model_service.transformer_feature_keys:
                feature_names = model_service.transformer_feature_keys
            else:
                feature_names = []
            
            data = {
                'total_features': len(feature_names),
                'feature_names': feature_names[:20] if len(feature_names) > 20 else feature_names,
                'feature_categories': {
                    'instructions': 'Instruction counts and types',
                    'control_flow': 'Branches, loops, and control structures',
                    'memory': 'Load/store operations and memory usage',
                    'arithmetic': 'Arithmetic and logical operations',
                    'functions': 'Function calls and characteristics',
                    'types': 'Data type usage'
                },
                'extraction_method': 'LLVM IR analysis',
                'target_architecture': 'RISC-V (riscv64)'
            }
            
            processing_time_ms = (time.time() - start_time) * 1000
            return success_response(data, processing_time_ms=processing_time_ms)
        
        except Exception as e:
            logger.error(f"Failed to get feature info: {e}")
            return error_response(
                f"Failed to retrieve feature information: {str(e)}",
                status_code=500,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @bp.route('/passes', methods=['GET'])
    def get_passes_info():
        """
        Get information about available LLVM passes.
        
        Returns:
            JSON with LLVM pass information
        """
        start_time = time.time()
        
        try:
            # Common LLVM passes with descriptions
            common_passes = {
                'mem2reg': 'Promote memory to register',
                'instcombine': 'Combine redundant instructions',
                'reassociate': 'Reassociate expressions',
                'gvn': 'Global value numbering',
                'sccp': 'Sparse conditional constant propagation',
                'dce': 'Dead code elimination',
                'simplifycfg': 'Simplify control flow graph',
                'licm': 'Loop invariant code motion',
                'loop-unroll': 'Unroll loops',
                'inline': 'Function inlining',
                'globalopt': 'Global optimization',
                'deadargelim': 'Dead argument elimination',
                'argpromotion': 'Argument promotion',
                'tailcallelim': 'Tail call elimination',
                'jump-threading': 'Jump threading',
                'correlated-propagation': 'Correlated value propagation',
                'dse': 'Dead store elimination',
                'adce': 'Aggressive dead code elimination',
                'bdce': 'Bit-tracking dead code elimination',
                'sroa': 'Scalar replacement of aggregates'
            }
            
            data = {
                'total_passes': len(common_passes),
                'common_passes': common_passes,
                'optimization_levels': {
                    '-O0': 'No optimization',
                    '-O1': 'Basic optimization',
                    '-O2': 'Moderate optimization',
                    '-O3': 'Aggressive optimization'
                },
                'ml_approach': 'ML models predict optimal pass sequences for specific programs'
            }
            
            processing_time_ms = (time.time() - start_time) * 1000
            return success_response(data, processing_time_ms=processing_time_ms)
        
        except Exception as e:
            logger.error(f"Failed to get passes info: {e}")
            return error_response(
                f"Failed to retrieve passes information: {str(e)}",
                status_code=500,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    @bp.route('/system', methods=['GET'])
    def get_system_info():
        """
        Get system capabilities and tool versions.
        
        Returns:
            JSON with system information
        """
        start_time = time.time()
        
        try:
            import subprocess
            import shutil
            
            def check_tool(tool_name):
                """Check if a tool is available"""
                return shutil.which(tool_name) is not None
            
            def get_version(tool_cmd):
                """Try to get tool version"""
                try:
                    result = subprocess.run(
                        tool_cmd,
                        capture_output=True,
                        timeout=2,
                        text=True
                    )
                    return result.stdout.split('\n')[0] if result.stdout else "Unknown"
                except:
                    return "Unknown"
            
            tools_status = {
                'clang': check_tool('clang'),
                'opt': check_tool('opt'),
                'llc': check_tool('llc'),
                'riscv64-gcc': check_tool('riscv64-linux-gnu-gcc'),
                'qemu-riscv64': check_tool('qemu-riscv64')
            }
            
            # Get versions for available tools
            versions = {}
            if tools_status['clang']:
                versions['clang'] = get_version(['clang', '--version'])
            if tools_status['qemu-riscv64']:
                versions['qemu'] = get_version(['qemu-riscv64', '--version'])
            
            data = {
                'tools_available': tools_status,
                'all_tools_ready': all(tools_status.values()),
                'versions': versions,
                'target_architecture': 'RISC-V 64-bit',
                'compilation_support': 'Cross-compilation with QEMU emulation',
                'python_version': f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}"
            }
            
            processing_time_ms = (time.time() - start_time) * 1000
            return success_response(data, processing_time_ms=processing_time_ms)
        
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return error_response(
                f"Failed to retrieve system information: {str(e)}",
                status_code=500,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    return bp
