#!/usr/bin/env python3
"""
Model Service - Handles ML model loading and inference
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import torch
import numpy as np
import joblib

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from iris import load_model, beam_search_decode

from config import ModelConfig, ErrorMessages
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelService:
    """Service for managing ML models"""
    
    def __init__(self):
        """Initialize model service"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Model storage
        self.transformer_model = None
        self.transformer_vocab = None
        self.transformer_feature_keys = None
        self.transformer_feature_scaler = None
        
        self.xgboost_model = None
        
        # Load models
        self._load_transformer_model()
        self._load_xgboost_model()
    
    def _load_transformer_model(self):
        """Load Transformer model"""
        try:
            model_path = ModelConfig.TRANSFORMER_BINARY_SIZE_MODEL
            if not model_path.exists():
                model_path = ModelConfig.TRANSFORMER_RUNTIME_MODEL
            
            if not model_path.exists():
                logger.warning(f"Transformer model not found at {model_path}")
                return
            
            logger.info(f"Loading Transformer model from {model_path}")
            
            self.transformer_model, self.transformer_vocab, \
            self.transformer_feature_keys, self.transformer_feature_scaler = \
                load_model(str(model_path), self.device)
            
            logger.info("✓ Transformer model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Transformer model: {e}")
            self.transformer_model = None
    
    def _load_xgboost_model(self):
        """Load XGBoost model"""
        try:
            model_path = ModelConfig.XGBOOST_MODEL
            
            if not model_path.exists():
                logger.warning(f"XGBoost model not found at {model_path}")
                return
            
            logger.info(f"Loading XGBoost model from {model_path}")
            self.xgboost_model = joblib.load(model_path)
            logger.info("✓ XGBoost model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load XGBoost model: {e}")
            self.xgboost_model = None
    
    def is_model_available(self, model_type: str) -> bool:
        """
        Check if a model is available.
        
        Args:
            model_type: 'transformer' or 'xgboost'
        
        Returns:
            True if model is loaded and available
        """
        if model_type == 'transformer':
            return self.transformer_model is not None
        elif model_type == 'xgboost':
            return self.xgboost_model is not None
        else:
            return False
    
    def predict_with_transformer(self, features: Dict) -> Tuple[bool, Optional[List[str]], Optional[str]]:
        """
        Predict pass sequence using Transformer model.
        
        Args:
            features: Extracted features dictionary
        
        Returns:
            Tuple of (success, predicted_passes, error_message)
        """
        if not self.is_model_available('transformer'):
            return False, None, ErrorMessages.MODEL_NOT_AVAILABLE.format('transformer')
        
        try:
            logger.debug("Running Transformer inference")
            
            predicted_passes = beam_search_decode(
                self.transformer_model,
                features,
                self.transformer_feature_keys,
                self.transformer_feature_scaler,
                self.transformer_vocab,
                self.device
            )
            
            logger.info(f"Predicted {len(predicted_passes)} passes")
            return True, predicted_passes, None
            
        except Exception as e:
            error_msg = f"Transformer inference failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def predict_with_xgboost(self, features: Dict) -> Tuple[bool, Optional[List[str]], Optional[str]]:
        """
        Predict pass sequence using XGBoost model.
        
        Args:
            features: Extracted features dictionary
        
        Returns:
            Tuple of (success, predicted_passes, error_message)
        """
        if not self.is_model_available('xgboost'):
            return False, None, ErrorMessages.MODEL_NOT_AVAILABLE.format('xgboost')
        
        try:
            logger.debug("Running XGBoost inference")
            
            # Convert features to DataFrame
            import pandas as pd
            features_df = pd.DataFrame([features], columns=self.transformer_feature_keys)
            
            # Predict
            prediction_str = self.xgboost_model.predict(features_df)[0]
            predicted_passes = prediction_str.split()
            
            logger.info(f"Predicted {len(predicted_passes)} passes")
            return True, predicted_passes, None
            
        except Exception as e:
            error_msg = f"XGBoost inference failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def predict(self, features: Dict, model_type: str = 'transformer') -> Tuple[bool, Optional[List[str]], Optional[str]]:
        """
        Predict pass sequence using specified model.
        
        Args:
            features: Extracted features dictionary
            model_type: 'transformer' or 'xgboost'
        
        Returns:
            Tuple of (success, predicted_passes, error_message)
        """
        if model_type == 'transformer':
            return self.predict_with_transformer(features)
        elif model_type == 'xgboost':
            return self.predict_with_xgboost(features)
        else:
            return False, None, ErrorMessages.INVALID_MODEL_SELECTION.format(
                ', '.join(ModelConfig.AVAILABLE_MODELS)
            )
    
    def get_model_info(self) -> Dict:
        """
        Get information about loaded models.
        
        Returns:
            Dictionary with model information
        """
        return {
            'transformer': {
                'available': self.is_model_available('transformer'),
                'path': str(ModelConfig.TRANSFORMER_BINARY_SIZE_MODEL),
                'device': str(self.device),
                'vocab_size': len(self.transformer_vocab) if self.transformer_vocab else 0,
                'num_features': len(self.transformer_feature_keys) if self.transformer_feature_keys else 0
            },
            'xgboost': {
                'available': self.is_model_available('xgboost'),
                'path': str(ModelConfig.XGBOOST_MODEL),
            }
        }
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models.
        
        Returns:
            List of available model names
        """
        available = []
        if self.is_model_available('transformer'):
            available.append('transformer')
        if self.is_model_available('xgboost'):
            available.append('xgboost')
        return available
