#!/usr/bin/env python3
"""
Feature Service - Handles LLVM IR feature extraction
"""

import sys
import os
from pathlib import Path
from typing import Dict, Tuple, Optional
import time

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'tools'))

from feature_extractor import extract_features_from_c_source, LLVMFeatureExtractor

from config import CompilationConfig, ErrorMessages
from utils.logger import get_logger

logger = get_logger(__name__)


class FeatureService:
    """Service for feature extraction from source code"""
    
    def __init__(self, target_arch: str = CompilationConfig.DEFAULT_TARGET_ARCH):
        """
        Initialize feature service.
        
        Args:
            target_arch: Target architecture for compilation
        """
        self.target_arch = target_arch
        self.extractor = LLVMFeatureExtractor()
        logger.info(f"FeatureService initialized for {target_arch}")
    
    def extract_from_file(self, source_file: Path) -> Tuple[bool, Optional[Dict], Optional[str], float]:
        """
        Extract features from C source file.
        
        Args:
            source_file: Path to C source file
        
        Returns:
            Tuple of (success, features_dict, error_message, extraction_time_ms)
        """
        start_time = time.time()
        
        try:
            logger.info(f"Extracting features from {source_file}")
            
            features = extract_features_from_c_source(
                str(source_file),
                target_arch=self.target_arch
            )
            
            extraction_time = (time.time() - start_time) * 1000
            logger.info(f"Feature extraction completed in {extraction_time:.2f}ms")
            logger.debug(f"Extracted {len(features)} features")
            
            return True, features, None, extraction_time
            
        except RuntimeError as e:
            error_msg = ErrorMessages.COMPILATION_FAILED.format(str(e))
            logger.error(error_msg)
            extraction_time = (time.time() - start_time) * 1000
            return False, None, error_msg, extraction_time
            
        except Exception as e:
            error_msg = f"Feature extraction failed: {str(e)}"
            logger.error(error_msg)
            extraction_time = (time.time() - start_time) * 1000
            return False, None, error_msg, extraction_time
    
    def extract_from_source_code(
        self,
        source_code: str,
        temp_file_path: Path
    ) -> Tuple[bool, Optional[Dict], Optional[str], float]:
        """
        Extract features from source code string.
        
        Args:
            source_code: C source code as string
            temp_file_path: Temporary file path to write code to
        
        Returns:
            Tuple of (success, features_dict, error_message, extraction_time_ms)
        """
        try:
            # Write source code to temporary file
            temp_file_path.write_text(source_code)
            logger.debug(f"Written source code to {temp_file_path}")
            
            # Extract features from file
            return self.extract_from_file(temp_file_path)
            
        except Exception as e:
            error_msg = f"Failed to process source code: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg, 0.0
    
    def extract_from_ir(self, ir_file: Path) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Extract features from LLVM IR file (.ll or .bc).
        
        Args:
            ir_file: Path to LLVM IR file
        
        Returns:
            Tuple of (success, features_dict, error_message)
        """
        try:
            logger.info(f"Extracting features from IR file {ir_file}")
            
            features = self.extractor.extract_from_file(str(ir_file))
            
            logger.info(f"Extracted {len(features)} features from IR")
            return True, features, None
            
        except Exception as e:
            error_msg = f"IR feature extraction failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def get_feature_info(self, features: Dict) -> Dict:
        """
        Get metadata about extracted features.
        
        Args:
            features: Extracted features dictionary
        
        Returns:
            Feature metadata dictionary
        """
        if not features:
            return {
                'feature_count': 0,
                'feature_names': [],
                'categories': {}
            }
        
        # Categorize features
        categories = {
            'instructions': [],
            'control_flow': [],
            'memory': [],
            'arithmetic': [],
            'types': [],
            'functions': [],
            'other': []
        }
        
        for key in features.keys():
            key_lower = key.lower()
            if 'num_' in key_lower or 'total_' in key_lower:
                if any(x in key_lower for x in ['br', 'switch', 'select', 'phi', 'icmp', 'fcmp']):
                    categories['control_flow'].append(key)
                elif any(x in key_lower for x in ['load', 'store', 'alloca', 'mem']):
                    categories['memory'].append(key)
                elif any(x in key_lower for x in ['add', 'sub', 'mul', 'div', 'rem', 'and', 'or', 'xor', 'shl', 'shr']):
                    categories['arithmetic'].append(key)
                elif 'function' in key_lower or 'call' in key_lower:
                    categories['functions'].append(key)
                elif 'uses_' in key_lower:
                    categories['types'].append(key)
                else:
                    categories['instructions'].append(key)
            else:
                categories['other'].append(key)
        
        return {
            'feature_count': len(features),
            'feature_names': list(features.keys()),
            'categories': {k: len(v) for k, v in categories.items()},
            'category_details': categories
        }
    
    def validate_features(self, features: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate extracted features.
        
        Args:
            features: Features dictionary
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not features:
            return False, "No features extracted"
        
        if not isinstance(features, dict):
            return False, "Features must be a dictionary"
        
        # Check for expected feature types
        expected_features = [
            'total_instructions',
            'total_basic_blocks',
            'num_functions'
        ]
        
        missing = [f for f in expected_features if f not in features]
        if missing:
            return False, f"Missing expected features: {', '.join(missing)}"
        
        # Check for valid values
        for key, value in features.items():
            if not isinstance(value, (int, float)):
                return False, f"Feature '{key}' has invalid type: {type(value)}"
            
            if value < 0:
                return False, f"Feature '{key}' has negative value: {value}"
        
        return True, None
