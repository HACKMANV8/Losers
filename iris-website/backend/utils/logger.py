#!/usr/bin/env python3
"""
Simple logging configuration for IRis Backend (Simplified)
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logger(
    name: str = "iris_backend",
    log_level: str = "INFO",
    log_file: Path = None
) -> logging.Logger:
    """
    Set up logger with file and console handlers.
    
    Args:
        name: Logger name
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
    
    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Set log level
    level = log_level or "INFO"
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (with rotation)
    if log_file:
        # Ensure log directory exists
        file_path = Path("logs") / f"{name}.log"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = "iris_backend") -> logging.Logger:
    """
    Get existing logger or create new one.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
