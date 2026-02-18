"""
Monitoring Utilities and Decorators
Helper functions and decorators for monitoring
"""

import functools
import time
import threading
from typing import Callable, Any, Optional, Dict
from datetime import datetime
from contextlib import contextmanager


def make_metric_name(component: str, operation: str, suffix: str = "") -> str:
    """Create standardized metric name"""
    base = f"{component}_{operation}"
    if suffix:
        return f"{base}_{suffix}"
    return base


def make_log_message(component: str, operation: str, status: str,
                    duration_ms: float = None, details: Dict = None) -> str:
    """Create standardized log message"""
    msg = f"[{component.upper()}] {operation} - {status}"
    
    if duration_ms is not None:
        msg += f" ({duration_ms:.2f}ms)"
    
    if details:
        details_str = ", ".join(f"{k}={v}" for k, v in details.items())
        msg += f" | {details_str}"
    
    return msg


class MetricDecorator:
    """Base metric decorator"""
    
    def __init__(self, metrics_collector: Optional[Any] = None):
        """Initialize metric decorator"""
        self.metrics = metrics_collector
    
    def set_metrics_collector(self, collector: Any):
        """Set metrics collector"""
        self.metrics = collector


class TrackExecution(MetricDecorator):
    """Decorator to track function execution"""
    
    def __init__(self, component: str = "app", metrics_collector: Optional[Any] = None):
        """Initialize tracker"""
        super().__init__(metrics_collector)
        self.component = component
    
    def __call__(self, func: Callable) -> Callable:
        """Decorate function"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            operation = func.__name__
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Record success metric
                if self.metrics:
                    try:
                        self.metrics.increment_counter(
                            make_metric_name(self.component, operation, "calls"),
                            labels={"status": "success"}
                        )
                        self.metrics.observe_histogram(
                            make_metric_name(self.component, operation, "duration_ms"),
                            duration_ms
                        )
                    except:
                        pass
                
                return result
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Record error metric
                if self.metrics:
                    try:
                        self.metrics.increment_counter(
                            make_metric_name(self.component, operation, "calls"),
                            labels={"status": "error"}
                        )
                        self.metrics.observe_histogram(
                            make_metric_name(self.component, operation, "duration_ms"),
                            duration_ms
                        )
                    except:
                        pass
                
                raise
        
        return wrapper


class TrackTiming(MetricDecorator):
    """Decorator to track timing percentiles"""
    
    def __init__(self, component: str = "app",
                 metrics_collector: Optional[Any] = None):
        """Initialize timing tracker"""
        super().__init__(metrics_collector)
        self.component = component
    
    def __call__(self, func: Callable) -> Callable:
        """Decorate function"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            operation = func.__name__
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if self.metrics:
                    try:
                        # Record as summary for percentile tracking
                        self.metrics.observe_summary(
                            make_metric_name(self.component, operation, "time_ms"),
                            duration_ms
                        )
                    except:
                        pass
                
                return result
            
            except Exception as e:
                raise
        
        return wrapper


class CountCalls(MetricDecorator):
    """Decorator to count function calls"""
    
    def __init__(self, component: str = "app",
                 metrics_collector: Optional[Any] = None):
        """Initialize call counter"""
        super().__init__(metrics_collector)
        self.component = component
    
    def __call__(self, func: Callable) -> Callable:
        """Decorate function"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            operation = func.__name__
            
            if self.metrics:
                try:
                    self.metrics.increment_counter(
                        make_metric_name(self.component, operation, "total"),
                        labels={"function": operation}
                    )
                except:
                    pass
            
            return func(*args, **kwargs)
        
        return wrapper


class TrackErrors(MetricDecorator):
    """Decorator to track function errors"""
    
    def __init__(self, component: str = "app",
                 metrics_collector: Optional[Any] = None):
        """Initialize error tracker"""
        super().__init__(metrics_collector)
        self.component = component
    
    def __call__(self, func: Callable) -> Callable:
        """Decorate function"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            operation = func.__name__
            
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                if self.metrics:
                    try:
                        self.metrics.increment_counter(
                            make_metric_name(self.component, operation, "errors"),
                            labels={"error_type": type(e).__name__}
                        )
                    except:
                        pass
                
                raise
        
        return wrapper


class LogFunction:
    """Decorator to log function calls"""
    
    def __init__(self, component: str = "app",
                 log_aggregator: Optional[Any] = None):
        """Initialize function logger"""
        self.component = component
        self.logs = log_aggregator
    
    def __call__(self, func: Callable) -> Callable:
        """Decorate function"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            operation = func.__name__
            start_time = time.time()
            
            try:
                if self.logs:
                    try:
                        self.logs.debug(
                            component=self.component,
                            message=f"Started: {operation}"
                        )
                    except:
                        pass
                
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if self.logs:
                    try:
                        self.logs.info(
                            component=self.component,
                            message=f"Completed: {operation} ({duration_ms:.2f}ms)"
                        )
                    except:
                        pass
                
                return result
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                if self.logs:
                    try:
                        self.logs.error(
                            component=self.component,
                            message=f"Failed: {operation}",
                            exception=str(e)
                        )
                    except:
                        pass
                
                raise
        
        return wrapper


class TraceFunction:
    """Decorator to trace function execution"""
    
    def __init__(self, component: str = "app",
                 tracing_collector: Optional[Any] = None):
        """Initialize function tracer"""
        self.component = component
        self.traces = tracing_collector
    
    def __call__(self, func: Callable) -> Callable:
        """Decorate function"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            operation = func.__name__
            
            # Start trace
            trace_id = None
            span_id = None
            if self.traces:
                try:
                    trace_id = self.traces.start_trace(
                        service=self.component,
                        request_id=f"{operation}_{int(time.time()*1000)}"
                    )
                    span_id = self.traces.start_span(
                        operation_name=operation,
                        component=self.component
                    )
                except:
                    pass
            
            try:
                result = func(*args, **kwargs)
                
                # End span successfully
                if self.traces and span_id:
                    try:
                        self.traces.end_span(span_id, "SUCCESS")
                        if trace_id:
                            self.traces.end_trace(trace_id)
                    except:
                        pass
                
                return result
            
            except Exception as e:
                # End span with error
                if self.traces and span_id:
                    try:
                        self.traces.end_span(
                            span_id, "ERROR",
                            error_details={"error": str(e)}
                        )
                        if trace_id:
                            self.traces.end_trace(trace_id)
                    except:
                        pass
                
                raise
        
        return wrapper


@contextmanager
def measure_time(component: str, operation: str, metrics_collector=None):
    """Context manager to measure operation time"""
    start_time = time.time()
    duration_ms = None
    
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        
        if metrics_collector:
            try:
                metrics_collector.observe_histogram(
                    make_metric_name(component, operation, "duration_ms"),
                    duration_ms
                )
            except:
                pass


@contextmanager
def count_operation(component: str, operation: str, metrics_collector=None):
    """Context manager to count operations"""
    try:
        yield
        
        if metrics_collector:
            try:
                metrics_collector.increment_counter(
                    make_metric_name(component, operation, "total"),
                    labels={"status": "success"}
                )
            except:
                pass
    
    except Exception as e:
        if metrics_collector:
            try:
                metrics_collector.increment_counter(
                    make_metric_name(component, operation, "total"),
                    labels={"status": "error"}
                )
            except:
                pass
        
        raise


def retry_with_tracking(max_retries: int = 3,
                       delay_seconds: float = 1.0,
                       backoff_multiplier: float = 2.0,
                       metrics_collector=None,
                       component: str = "app"):
    """Decorator to retry with exponential backoff and tracking"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            operation = func.__name__
            last_exception = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    if metrics_collector and attempt > 1:
                        try:
                            metrics_collector.increment_counter(
                                make_metric_name(component, operation, "retries"),
                                labels={"attempt": str(attempt)}
                            )
                        except:
                            pass
                    
                    return result
                
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = delay_seconds * (backoff_multiplier ** (attempt - 1))
                        time.sleep(delay)
                    
                    if metrics_collector:
                        try:
                            metrics_collector.increment_counter(
                                make_metric_name(component, operation, "retry_attempts"),
                                labels={"attempt": str(attempt)}
                            )
                        except:
                            pass
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def batch_operation(batch_size: int = 100,
                   timeout_seconds: float = 5.0):
    """Decorator to batch operations"""
    
    def decorator(func: Callable) -> Callable:
        batch_queue = []
        batch_lock = threading.Lock()
        
        @functools.wraps(func)
        def wrapper(item: Any) -> Any:
            nonlocal batch_queue
            
            with batch_lock:
                batch_queue.append(item)
                
                if len(batch_queue) >= batch_size:
                    items = batch_queue
                    batch_queue = []
                    return func(items)
            
            return None
        
        return wrapper
    return decorator
