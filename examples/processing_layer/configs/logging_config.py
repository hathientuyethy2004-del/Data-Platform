"""
Processing Layer - Logging Configuration
Centralized logging for Spark jobs
"""

import logging
import os
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler

# ============================================================================
# Logging Setup
# ============================================================================

def setup_logger(
    name: str,
    log_level: str = "INFO",
    console_output: bool = True,
    file_output: bool = True,
    log_dir: str = "/workspaces/Data-Platform/processing_layer/logs"
) -> logging.Logger:
    """
    Setup a logger with both console and file output
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Enable console output
        file_output: Enable file output
        log_dir: Directory for log files
        
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if needed
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", '
        '"message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", '
        '"line": %(lineno)d}'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler (rotating)
    if file_output:
        log_file = os.path.join(log_dir, f"{name.replace('.', '_')}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=104857600,  # 100MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


class ContextLogger:
    """
    Logger wrapper que allows attaching context (request_id, trace_id, etc.)
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.context = {}
    
    def set_context(self, **kwargs):
        """Set context variables"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear context"""
        self.context.clear()
    
    def _format_message(self, message: str) -> str:
        """Format message with context"""
        if self.context:
            context_str = " ".join([f"{k}={v}" for k, v in self.context.items()])
            return f"[{context_str}] {message}"
        return message
    
    def debug(self, message: str):
        self.logger.debug(self._format_message(message))
    
    def info(self, message: str):
        self.logger.info(self._format_message(message))
    
    def warning(self, message: str):
        self.logger.warning(self._format_message(message))
    
    def error(self, message: str):
        self.logger.error(self._format_message(message))
    
    def critical(self, message: str):
        self.logger.critical(self._format_message(message))
