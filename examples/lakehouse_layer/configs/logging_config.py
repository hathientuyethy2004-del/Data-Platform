"""
Lakehouse Logging Configuration
Centralized JSON logging for all lakehouse components
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add custom fields if present
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


def setup_logging(name: str, log_level: str = 'INFO') -> logging.Logger:
    """
    Setup logger for lakehouse components
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    # Create logs directory
    logs_dir = os.getenv('LOGS_DIR', '/var/lib/lakehouse/logs')
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # File handler (JSON format)
    log_file = os.path.join(logs_dir, f"{name}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Console handler (simple format)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


# Custom logging context manager for detailed operation tracking
class LogContext:
    """Context manager for operation logging"""
    
    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.info(
            f"▶️  Starting {self.operation}",
            extra={'extra': {'operation': self.operation, **self.kwargs}}
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(
                f"✅ Completed {self.operation} ({duration:.2f}s)",
                extra={'extra': {'operation': self.operation, 'duration_seconds': duration}}
            )
        else:
            self.logger.error(
                f"❌ Failed {self.operation}: {exc_val}",
                extra={'extra': {'operation': self.operation, 'error': str(exc_val)}}
            )
        
        return False  # Re-raise exceptions
