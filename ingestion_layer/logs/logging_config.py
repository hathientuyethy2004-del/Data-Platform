"""
Centralized Logging Configuration
Quản lý logging cho toàn bộ ingestion layer
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# Create logs directory nếu chưa tồn tại
LOG_DIR = Path("/workspaces/Data-Platform/ingestion_layer/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class JSONFormatter(logging.Formatter):
    """JSON formatter cho structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record thành JSON"""
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_obj.update(record.extra_fields)
        
        return json.dumps(log_obj, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.RESET)
        
        # Format base message
        log_format = (
            f"{color}[%(asctime)s]{self.RESET} "
            f"{color}[%(levelname)s]{self.RESET} "
            f"%(name)s: %(message)s"
        )
        
        formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


def setup_logger(
    name: str,
    log_level: str = 'INFO',
    console_output: bool = True,
    file_output: bool = True,
    json_format: bool = False,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup logger với optional file output, console output, JSON format
    
    Args:
        name: Logger name
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Print to console
        file_output: Write to file
        json_format: Use JSON formatter for files
        log_file: Custom log file name
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Set log level from environment if available
    env_level = os.getenv('LOG_LEVEL', log_level)
    log_level_int = getattr(logging, env_level.upper(), logging.INFO)
    logger.setLevel(log_level_int)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Console handler (always colored)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level_int)
        console_formatter = ColoredFormatter()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler (with rotation)
    if file_output:
        if log_file is None:
            log_file = f"{name.replace('.', '_')}.log"
        
        log_path = LOG_DIR / log_file
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level_int)
        
        if json_format:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        logger.debug(f"File logging enabled: {log_path}")
    
    return logger


def setup_root_logger(
    log_level: str = 'INFO',
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    Setup root logger
    
    Args:
        log_level: Root log level
        console_output: Print to console
        file_output: Write root.log
        
    Returns:
        Root logger
    """
    return setup_logger(
        name='root',
        log_level=log_level,
        console_output=console_output,
        file_output=file_output,
        json_format=False,
        log_file='root.log'
    )


class ContextLogger:
    """
    Logger wrapper that tracks context (request_id, trace_id, etc.)
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.context = {}
    
    def set_context(self, **kwargs):
        """Set context fields"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear context"""
        self.context.clear()
    
    def _log(self, level: str, msg: str, *args, **kwargs):
        """Internal log method with context"""
        extra = kwargs.pop('extra', {})
        if self.context:
            extra.update(self.context)
        
        if extra:
            # Create a LogRecord with extra fields
            record = self.logger.makeRecord(
                self.logger.name,
                getattr(logging, level),
                "(unknown file)",
                0,
                msg,
                args,
                None,
                **kwargs
            )
            record.extra_fields = extra
            self.logger.handle(record)
        else:
            getattr(self.logger, level.lower())(msg, *args, **kwargs)
    
    def debug(self, msg, *args, **kwargs):
        self._log('DEBUG', msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        self._log('INFO', msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        self._log('WARNING', msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        self._log('ERROR', msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        self._log('CRITICAL', msg, *args, **kwargs)


# Initialize root logger on module import
root_logger = setup_root_logger()


if __name__ == "__main__":
    # Test setup
    test_logger = setup_logger(
        'test_app',
        log_level='DEBUG',
        json_format=True
    )
    
    test_logger.debug("🔧 Debug message")
    test_logger.info("ℹ️  Info message")
    test_logger.warning("⚠️  Warning message")
    test_logger.error("❌ Error message")
    
    # Test context logger
    ctx_logger = ContextLogger(test_logger)
    ctx_logger.set_context(request_id="123", user_id="456")
    ctx_logger.info("Message with context")
    
    print("\n✅ Logs written to: " + str(LOG_DIR))
