"""
Distributed Tracing System
End-to-end request/pipeline tracing across components
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import threading

from threading import Lock, local


@dataclass
class Span:
    """Distributed trace span"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    component: str
    start_time: str
    end_time: str = ""
    duration_ms: float = 0.0
    status: str = "RUNNING"  # RUNNING, SUCCESS, ERROR
    attributes: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    events: List[Dict] = field(default_factory=list)
    error_details: str = ""


@dataclass
class Trace:
    """Complete distributed trace"""
    trace_id: str
    root_span_id: str
    start_time: str
    end_time: str = ""
    duration_ms: float = 0.0
    status: str = "RUNNING"
    service: str = ""
    request_id: str = ""
    spans: List[Span] = field(default_factory=list)
    messages: Dict[str, int] = field(default_factory=dict)


class TracingCollector:
    """Distributed tracing system"""

    def __init__(self, storage_path: str = "/tmp/monitoring/traces"):
        """Initialize tracing collector"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.traces: Dict[str, Trace] = {}
        self.spans: Dict[str, Span] = {}
        self.lock = Lock()
        
        # Thread-local context for trace_id and span_id
        self.context = local()
        
        self._load_traces()

    def start_trace(self, operation_name: str, service: str = "",
                   request_id: str = "") -> str:
        """Start a new trace"""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        trace = Trace(
            trace_id=trace_id,
            root_span_id=span_id,
            start_time=datetime.now().isoformat(),
            service=service,
            request_id=request_id
        )
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=None,
            operation_name=operation_name,
            component=service,
            start_time=datetime.now().isoformat()
        )
        
        with self.lock:
            self.traces[trace_id] = trace
            self.spans[span_id] = span
            trace.spans.append(span)
        
        # Set thread-local context
        self.context.trace_id = trace_id
        self.context.span_id = span_id
        
        return trace_id

    def start_span(self, operation_name: str, component: str,
                  trace_id: str = None,
                  attributes: Dict[str, Any] = None) -> str:
        """Start a child span within a trace"""
        if trace_id is None:
            trace_id = getattr(self.context, 'trace_id', None)
        
        if trace_id is None or trace_id not in self.traces:
            # Create new trace from span
            trace_id = self.start_trace(operation_name, service=component)
            return self.context.span_id
        
        span_id = str(uuid.uuid4())
        parent_span_id = getattr(self.context, 'span_id', None)
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            component=component,
            start_time=datetime.now().isoformat(),
            attributes=attributes or {}
        )
        
        with self.lock:
            self.spans[span_id] = span
            self.traces[trace_id].spans.append(span)
        
        # Update context
        old_span_id = getattr(self.context, 'span_id', None)
        self.context.span_id = span_id
        
        return (span_id, old_span_id)  # Return new and old for context switching

    def add_event(self, event_name: str, attributes: Dict = None,
                 span_id: str = None):
        """Add event to a span"""
        if span_id is None:
            span_id = getattr(self.context, 'span_id', None)
        
        if span_id is None or span_id not in self.spans:
            return
        
        event = {
            "name": event_name,
            "timestamp": datetime.now().isoformat(),
            "attributes": attributes or {}
        }
        
        with self.lock:
            self.spans[span_id].events.append(event)

    def add_tag(self, key: str, value: str, span_id: str = None):
        """Add tag to span"""
        if span_id is None:
            span_id = getattr(self.context, 'span_id', None)
        
        if span_id is None or span_id not in self.spans:
            return
        
        with self.lock:
            self.spans[span_id].tags[key] = value

    def end_span(self, span_id: str = None, status: str = "SUCCESS",
                error_details: str = ""):
        """End a span"""
        if span_id is None:
            span_id = getattr(self.context, 'span_id', None)
        
        if span_id is None or span_id not in self.spans:
            return
        
        with self.lock:
            span = self.spans[span_id]
            span.end_time = datetime.now().isoformat()
            span.status = status
            span.error_details = error_details
            
            # Calculate duration
            start = datetime.fromisoformat(span.start_time)
            end = datetime.fromisoformat(span.end_time)
            span.duration_ms = (end - start).total_seconds() * 1000

    def end_trace(self, trace_id: str = None, status: str = "SUCCESS"):
        """End a trace"""
        if trace_id is None:
            trace_id = getattr(self.context, 'trace_id', None)
        
        if trace_id is None or trace_id not in self.traces:
            return
        
        with self.lock:
            trace = self.traces[trace_id]
            trace.end_time = datetime.now().isoformat()
            trace.status = status
            
            # Calculate total duration
            start = datetime.fromisoformat(trace.start_time)
            end = datetime.fromisoformat(trace.end_time)
            trace.duration_ms = (end - start).total_seconds() * 1000
            
            # Count messages by status
            for span in trace.spans:
                trace.messages[span.status] = trace.messages.get(span.status, 0) + 1
        
        # Clear context
        self.context.trace_id = None
        self.context.span_id = None
        
        self._save_traces()

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get trace details"""
        return self.traces.get(trace_id)

    def get_traces_by_service(self, service: str, days: int = 1) -> List[Trace]:
        """Get traces for a specific service"""
        cutoff = datetime.now() - timedelta(days=days)
        traces = []
        
        for trace in self.traces.values():
            if trace.service == service:
                trace_time = datetime.fromisoformat(trace.start_time)
                if trace_time >= cutoff:
                    traces.append(trace)
        
        return sorted(traces, key=lambda t: t.start_time, reverse=True)

    def get_slow_traces(self, min_duration_ms: float = 1000,
                       limit: int = 10) -> List[Trace]:
        """Get slowest traces"""
        slow = [
            t for t in self.traces.values()
            if t.duration_ms >= min_duration_ms and t.end_time
        ]
        
        return sorted(
            slow,
            key=lambda t: t.duration_ms,
            reverse=True
        )[:limit]

    def get_error_traces(self, limit: int = 10) -> List[Trace]:
        """Get traces with errors"""
        errors = [
            t for t in self.traces.values()
            if t.status == "ERROR"
        ]
        
        return sorted(
            errors,
            key=lambda t: t.start_time,
            reverse=True
        )[:limit]

    def get_tracing_statistics(self) -> Dict:
        """Get tracing statistics"""
        total_traces = len(self.traces)
        completed_traces = sum(1 for t in self.traces.values() if t.end_time)
        error_traces = sum(1 for t in self.traces.values() if t.status == "ERROR")
        
        durations = [
            t.duration_ms for t in self.traces.values()
            if t.duration_ms > 0
        ]
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        
        # Get by service
        by_service = defaultdict(int)
        for trace in self.traces.values():
            by_service[trace.service] += 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_traces": total_traces,
            "completed_traces": completed_traces,
            "error_traces": error_traces,
            "error_rate": error_traces / max(total_traces, 1),
            "average_duration_ms": avg_duration,
            "max_duration_ms": max_duration,
            "min_duration_ms": min_duration,
            "by_service": dict(by_service),
            "total_spans": len(self.spans)
        }

    def export_trace(self, trace_id: str, export_path: str) -> bool:
        """Export trace to JSON"""
        try:
            trace = self.traces.get(trace_id)
            if not trace:
                return False
            
            export_data = {
                "trace_id": trace.trace_id,
                "service": trace.service,
                "request_id": trace.request_id,
                "status": trace.status,
                "duration_ms": trace.duration_ms,
                "start_time": trace.start_time,
                "end_time": trace.end_time,
                "spans": [asdict(span) for span in trace.spans]
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting trace: {e}")
            return False

    def visualize_trace(self, trace_id: str) -> Dict:
        """Get trace visualization data"""
        trace = self.traces.get(trace_id)
        if not trace:
            return {}
        
        # Build span tree
        roots = [s for s in trace.spans if s.parent_span_id is None]
        
        def build_tree(span):
            children = [
                build_tree(s) for s in trace.spans
                if s.parent_span_id == span.span_id
            ]
            
            return {
                "span_id": span.span_id,
                "operation": span.operation_name,
                "component": span.component,
                "duration_ms": span.duration_ms,
                "status": span.status,
                "children": children,
                "start_time": span.start_time
            }
        
        tree = [build_tree(root) for root in roots]
        
        return {
            "trace_id": trace_id,
            "status": trace.status,
            "total_duration_ms": trace.duration_ms,
            "span_tree": tree,
            "total_spans": len(trace.spans)
        }

    def clean_old_traces(self, days: int = 7):
        """Remove traces older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.lock:
            original_count = len(self.traces)
            traces_to_delete = []
            
            for trace_id, trace in self.traces.items():
                trace_time = datetime.fromisoformat(trace.start_time)
                if trace_time < cutoff:
                    traces_to_delete.append(trace_id)
            
            for trace_id in traces_to_delete:
                trace = self.traces.pop(trace_id)
                # Remove spans
                for span in trace.spans:
                    self.spans.pop(span.span_id, None)
            
            removed = original_count - len(self.traces)
            if removed > 0:
                print(f"Cleaned {removed} old traces (older than {days} days)")
                self._save_traces()

    def _load_traces(self):
        """Load traces from storage"""
        traces_file = self.storage_path / "traces.json"
        if traces_file.exists():
            try:
                with open(traces_file, 'r') as f:
                    data = json.load(f)
                    for trace_data in data:
                        spans_data = trace_data.pop('spans', [])
                        trace = Trace(**trace_data)
                        
                        for span_data in spans_data:
                            span = Span(**span_data)
                            trace.spans.append(span)
                            self.spans[span.span_id] = span
                        
                        self.traces[trace.trace_id] = trace
            except Exception as e:
                print(f"Error loading traces: {e}")

    def _save_traces(self):
        """Save traces to storage"""
        try:
            traces_file = self.storage_path / "traces.json"
            # Keep only completed traces
            completed = [
                t for t in self.traces.values()
                if t.end_time
            ]
            
            # Limit to last 10000 traces
            to_save = completed[-10000:] if len(completed) > 10000 else completed
            
            data = []
            for trace in to_save:
                trace_dict = asdict(trace)
                data.append(trace_dict)
            
            with open(traces_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving traces: {e}")


# Global tracing collector instance
_tracing_collector = None

def get_tracing_collector(storage_path: str = "/tmp/monitoring/traces") -> TracingCollector:
    """Get or create global tracing collector"""
    global _tracing_collector
    if _tracing_collector is None:
        _tracing_collector = TracingCollector(storage_path)
    return _tracing_collector
