#!/usr/bin/env python3
"""
Logging configuration for IRis Backend
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from config import LoggingConfig


def setup_logger(
    name: str = "iris_backend",
    log_level: str = None,
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
    level = log_level or LoggingConfig.LOG_LEVEL
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(LoggingConfig.LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (with rotation)
    if log_file or LoggingConfig.LOG_FILE:
        file_path = log_file or LoggingConfig.LOG_FILE
        
        # Ensure log directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=LoggingConfig.LOG_MAX_BYTES,
            backupCount=LoggingConfig.LOG_BACKUP_COUNT
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
