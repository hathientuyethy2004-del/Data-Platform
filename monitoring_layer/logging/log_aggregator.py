"""
Centralized Logging System
Aggregates logs from all platform components
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import threading

from threading import Lock


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEvent:
    """Log event record"""
    timestamp: str
    level: str
    component: str
    message: str
    trace_id: str = ""
    context: Dict = None
    exception: str = ""
    duration_ms: float = 0.0
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


class LogAggregator:
    """Centralized log aggregation system"""

    def __init__(self, storage_path: str = "/tmp/monitoring/logs"):
        """Initialize log aggregator"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.logs: List[LogEvent] = []
        self.lock = Lock()
        
        # Component-specific logs
        self.component_logs: Dict[str, List[LogEvent]] = defaultdict(list)
        
        # Error aggregation
        self.error_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        self._load_logs()

    def log(self, level: str, component: str, message: str,
           trace_id: str = "", context: Dict = None,
           exception: str = "", duration_ms: float = 0.0) -> str:
        """Log an event"""
        log_event = LogEvent(
            timestamp=datetime.now().isoformat(),
            level=level,
            component=component,
            message=message,
            trace_id=trace_id,
            context=context or {},
            exception=exception,
            duration_ms=duration_ms
        )
        
        with self.lock:
            self.logs.append(log_event)
            self.component_logs[component].append(log_event)
            
            # Track errors
            if level in ["ERROR", "CRITICAL"]:
                error_key = f"{component}:{message[:50]}"
                self.error_counts[component][error_key] += 1
        
        # Save periodically
        if len(self.logs) % 100 == 0:
            self._save_logs()
        
        return log_event.timestamp

    def debug(self, component: str, message: str, context: Dict = None):
        """Log debug message"""
        self.log(LogLevel.DEBUG.value, component, message, context=context)

    def info(self, component: str, message: str, context: Dict = None):
        """Log info message"""
        self.log(LogLevel.INFO.value, component, message, context=context)

    def warning(self, component: str, message: str, context: Dict = None):
        """Log warning message"""
        self.log(LogLevel.WARNING.value, component, message, context=context)

    def error(self, component: str, message: str, context: Dict = None,
             exception: str = ""):
        """Log error message"""
        self.log(LogLevel.ERROR.value, component, message,
                context=context, exception=exception)

    def critical(self, component: str, message: str, context: Dict = None,
                exception: str = ""):
        """Log critical message"""
        self.log(LogLevel.CRITICAL.value, component, message,
                context=context, exception=exception)

    def get_logs(self, component: str = None, level: str = None,
                days: int = 7) -> List[LogEvent]:
        """Retrieve logs with filters"""
        cutoff = datetime.now() - timedelta(days=days)
        filtered = []
        
        source = self.component_logs.get(component, self.logs) if component else self.logs
        
        for log in source:
            log_time = datetime.fromisoformat(log.timestamp)
            if log_time < cutoff:
                continue
            
            if level and log.level != level:
                continue
            
            filtered.append(log)
        
        return filtered

    def get_error_summary(self, component: str = None, days: int = 7) -> Dict:
        """Get error summary"""
        cutoff = datetime.now() - timedelta(days=days)
        summary = {}
        
        if component:
            errors = self.error_counts.get(component, {})
            summary[component] = {
                "total_errors": sum(errors.values()),
                "unique_error_types": len(errors),
                "top_errors": sorted(
                    errors.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            }
        else:
            for comp in self.error_counts:
                errors = self.error_counts[comp]
                summary[comp] = {
                    "total_errors": sum(errors.values()),
                    "unique_error_types": len(errors),
                    "top_errors": sorted(
                        errors.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:3]
                }
        
        return summary

    def get_component_logs(self, component: str, limit: int = 100) -> List[Dict]:
        """Get logs for a specific component"""
        logs = self.component_logs.get(component, [])
        recent = logs[-limit:] if len(logs) > limit else logs
        
        return [asdict(log) for log in recent]

    def search_logs(self, search_query: str, component: str = None,
                   level: str = None) -> List[LogEvent]:
        """Search logs by message content"""
        results = []
        source = self.component_logs.get(component, self.logs) if component else self.logs
        
        for log in source:
            if search_query.lower() in log.message.lower():
                if level is None or log.level == level:
                    results.append(log)
        
        return results[-100:]  # Return last 100 matches

    def get_log_statistics(self) -> Dict:
        """Get log statistics"""
        total_logs = len(self.logs)
        level_counts = defaultdict(int)
        component_counts = defaultdict(int)
        
        for log in self.logs:
            level_counts[log.level] += 1
            component_counts[log.component] += 1
        
        # Get logs from last hour
        cutoff = datetime.now() - timedelta(hours=1)
        recent_logs = [
            log for log in self.logs
            if datetime.fromisoformat(log.timestamp) >= cutoff
        ]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_logs": total_logs,
            "logs_last_hour": len(recent_logs),
            "by_level": dict(level_counts),
            "by_component": dict(component_counts),
            "error_rate": (
                level_counts["ERROR"] + level_counts["CRITICAL"]
            ) / max(total_logs, 1),
            "components": list(component_counts.keys())
        }

    def export_logs(self, export_path: str, component: str = None,
                   days: int = 7) -> bool:
        """Export logs to JSON"""
        try:
            logs = self.get_logs(component=component, days=days)
            
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "filter": {"component": component, "days": days},
                "total_logs": len(logs),
                "logs": [asdict(log) for log in logs],
                "statistics": self.get_log_statistics(),
                "errors": self.get_error_summary(component=component, days=days)
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting logs: {e}")
            return False

    def create_python_logger(self, name: str) -> logging.Logger:
        """Create a Python logger that integrates with aggregator"""
        logger = logging.getLogger(name)
        
        class AggregatorHandler(logging.Handler):
            """Custom handler to forward logs to aggregator"""
            def __init__(self, aggregator, component_name):
                super().__init__()
                self.aggregator = aggregator
                self.component_name = component_name
            
            def emit(self, record):
                try:
                    level = record.levelname
                    message = record.getMessage()
                    context = {
                        "file": record.filename,
                        "function": record.funcName,
                        "line": record.lineno
                    }
                    
                    if record.exc_info:
                        exception = ''.join(
                            logging.Formatter().formatException(record.exc_info)
                        )
                    else:
                        exception = ""
                    
                    self.aggregator.log(
                        level, self.component_name, message,
                        context=context, exception=exception
                    )
                except Exception:
                    self.handleError(record)
        
        handler = AggregatorHandler(self, name)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        
        return logger

    def clean_old_logs(self, days: int = 30):
        """Remove logs older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.lock:
            original_count = len(self.logs)
            self.logs = [
                log for log in self.logs
                if datetime.fromisoformat(log.timestamp) >= cutoff
            ]
            removed = original_count - len(self.logs)
            
            # Also clean component logs
            for component in self.component_logs:
                self.component_logs[component] = [
                    log for log in self.component_logs[component]
                    if datetime.fromisoformat(log.timestamp) >= cutoff
                ]
            
            if removed > 0:
                print(f"Cleaned {removed} old log entries (older than {days} days)")
                self._save_logs()

    def _load_logs(self):
        """Load logs from storage"""
        logs_file = self.storage_path / "logs.json"
        if logs_file.exists():
            try:
                with open(logs_file, 'r') as f:
                    data = json.load(f)
                    for log_data in data:
                        log_event = LogEvent(**log_data)
                        self.logs.append(log_event)
                        self.component_logs[log_event.component].append(log_event)
            except Exception as e:
                print(f"Error loading logs: {e}")

    def _save_logs(self):
        """Save logs to storage"""
        try:
            logs_file = self.storage_path / "logs.json"
            # Keep only last 1000 logs in storage
            logs_to_save = self.logs[-1000:] if len(self.logs) > 1000 else self.logs
            
            with open(logs_file, 'w') as f:
                json.dump([asdict(log) for log in logs_to_save], f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving logs: {e}")


# Global log aggregator instance
_log_aggregator = None

def get_log_aggregator(storage_path: str = "/tmp/monitoring/logs") -> LogAggregator:
    """Get or create global log aggregator"""
    global _log_aggregator
    if _log_aggregator is None:
        _log_aggregator = LogAggregator(storage_path)
    return _log_aggregator
