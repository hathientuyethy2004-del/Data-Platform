"""
Metrics Collector System
Prometheus-compatible metrics collection for data platform monitoring
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import threading

from threading import Lock


class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"         # Monotonically increasing
    GAUGE = "gauge"             # Point-in-time value
    HISTOGRAM = "histogram"     # Distribution of values
    SUMMARY = "summary"         # Quantiles + count + sum


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: str
    value: float
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


@dataclass
class Metric:
    """Metric definition"""
    name: str
    type: str
    description: str
    unit: str = ""
    labels: List[str] = None
    created_at: str = ""
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class MetricsCollector:
    """Prometheus-compatible metrics collection"""

    def __init__(self, storage_path: str = "/tmp/monitoring/metrics"):
        """Initialize metrics collector"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.metrics: Dict[str, Metric] = {}
        self.data: Dict[str, List[MetricPoint]] = defaultdict(list)
        self.lock = Lock()
        
        self.counter_values: Dict[str, float] = {}
        self.gauge_values: Dict[str, float] = {}
        self.histogram_buckets: Dict[str, List[float]] = defaultdict(list)
        self.summary_values: Dict[str, List[float]] = defaultdict(list)
        
        self._load_metrics()

    def register_metric(self, name: str, type_: str, description: str,
                       unit: str = "", labels: List[str] = None) -> bool:
        """Register a new metric"""
        if name in self.metrics:
            return False
        
        metric = Metric(
            name=name,
            type=type_,
            description=description,
            unit=unit,
            labels=labels or []
        )
        
        self.metrics[name] = metric
        self._save_metrics()
        
        return True

    def increment_counter(self, name: str, value: float = 1.0,
                         labels: Dict[str, str] = None) -> bool:
        """Increment counter metric"""
        if name not in self.metrics or self.metrics[name].type != MetricType.COUNTER.value:
            return False
        
        with self.lock:
            key = self._make_key(name, labels)
            self.counter_values[key] = self.counter_values.get(key, 0) + value
            
            self._record_point(name, self.counter_values[key], labels)
        
        return True

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> bool:
        """Set gauge metric"""
        if name not in self.metrics or self.metrics[name].type != MetricType.GAUGE.value:
            return False
        
        with self.lock:
            key = self._make_key(name, labels)
            self.gauge_values[key] = value
            self._record_point(name, value, labels)
        
        return True

    def observe_histogram(self, name: str, value: float,
                         labels: Dict[str, str] = None) -> bool:
        """Record histogram observation"""
        if name not in self.metrics or self.metrics[name].type != MetricType.HISTOGRAM.value:
            return False
        
        with self.lock:
            key = self._make_key(name, labels)
            self.histogram_buckets[key].append(value)
            self._record_point(name, value, labels)
        
        return True

    def observe_summary(self, name: str, value: float,
                       labels: Dict[str, str] = None) -> bool:
        """Record summary observation"""
        if name not in self.metrics or self.metrics[name].type != MetricType.SUMMARY.value:
            return False
        
        with self.lock:
            key = self._make_key(name, labels)
            self.summary_values[key].append(value)
            self._record_point(name, value, labels)
        
        return True

    def get_metric_value(self, name: str, labels: Dict[str, str] = None) -> Optional[float]:
        """Get current metric value"""
        key = self._make_key(name, labels)
        
        metric = self.metrics.get(name)
        if not metric:
            return None
        
        if metric.type == MetricType.COUNTER.value:
            return self.counter_values.get(key)
        elif metric.type == MetricType.GAUGE.value:
            return self.gauge_values.get(key)
        elif metric.type == MetricType.HISTOGRAM.value:
            values = self.histogram_buckets.get(key, [])
            return sum(values) / len(values) if values else None
        elif metric.type == MetricType.SUMMARY.value:
            values = self.summary_values.get(key, [])
            return sum(values) / len(values) if values else None
        
        return None

    def get_metric_statistics(self, name: str, labels: Dict[str, str] = None) -> Dict:
        """Get detailed statistics for a metric"""
        key = self._make_key(name, labels)
        metric = self.metrics.get(name)
        
        if not metric:
            return {}
        
        if metric.type == MetricType.COUNTER.value:
            value = self.counter_values.get(key, 0)
            return {
                "name": name,
                "type": metric.type,
                "labels": labels,
                "current_value": value,
                "description": metric.description
            }
        
        elif metric.type == MetricType.GAUGE.value:
            value = self.gauge_values.get(key, 0)
            return {
                "name": name,
                "type": metric.type,
                "labels": labels,
                "current_value": value,
                "description": metric.description
            }
        
        elif metric.type == MetricType.HISTOGRAM.value:
            values = self.histogram_buckets.get(key, [])
            return {
                "name": name,
                "type": metric.type,
                "labels": labels,
                "count": len(values),
                "sum": sum(values),
                "mean": sum(values) / len(values) if values else 0,
                "min": min(values) if values else 0,
                "max": max(values) if values else 0,
                "p50": self._percentile(values, 50),
                "p95": self._percentile(values, 95),
                "p99": self._percentile(values, 99),
                "description": metric.description
            }
        
        elif metric.type == MetricType.SUMMARY.value:
            values = self.summary_values.get(key, [])
            return {
                "name": name,
                "type": metric.type,
                "labels": labels,
                "count": len(values),
                "sum": sum(values),
                "mean": sum(values) / len(values) if values else 0,
                "min": min(values) if values else 0,
                "max": max(values) if values else 0,
                "description": metric.description
            }
        
        return {}

    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        for name, metric in self.metrics.items():
            # Help line
            lines.append(f"# HELP {name} {metric.description}")
            # Type line
            lines.append(f"# TYPE {name} {metric.type}")
            
            # Data lines
            if metric.type == MetricType.COUNTER.value:
                for key, value in self.counter_values.items():
                    if key.startswith(f"{name}_"):
                        labels = self._parse_key(key)
                        lines.append(self._format_prometheus_line(name, value, labels))
            
            elif metric.type == MetricType.GAUGE.value:
                for key, value in self.gauge_values.items():
                    if key.startswith(f"{name}_"):
                        labels = self._parse_key(key)
                        lines.append(self._format_prometheus_line(name, value, labels))
        
        return "\n".join(lines)

    def get_platform_metrics(self) -> Dict[str, Any]:
        """Get all platform metrics summary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "registered_metrics": len(self.metrics),
            "metrics_by_type": self._count_metrics_by_type(),
            "current_values": self._get_all_current_values(),
            "data_points_count": sum(len(points) for points in self.data.values())
        }

    def clean_old_data(self, days: int = 7):
        """Remove data older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.lock:
            for metric_name in self.data:
                original_count = len(self.data[metric_name])
                self.data[metric_name] = [
                    point for point in self.data[metric_name]
                    if datetime.fromisoformat(point.timestamp) >= cutoff
                ]
                removed = original_count - len(self.data[metric_name])
                if removed > 0:
                    print(f"Cleaned {removed} old points from {metric_name}")

    def export_metrics(self, export_path: str) -> bool:
        """Export all metrics data"""
        try:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {name: asdict(m) for name, m in self.metrics.items()},
                "data_points": {
                    name: [asdict(p) for p in points]
                    for name, points in self.data.items()
                },
                "current_values": self._get_all_current_values()
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting metrics: {e}")
            return False

    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create unique key for metric with labels"""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}_{label_str}"

    def _parse_key(self, key: str) -> Dict[str, str]:
        """Parse key back to labels"""
        if "_" not in key:
            return {}
        
        parts = key.split("_", 1)
        if len(parts) < 2:
            return {}
        
        labels = {}
        for pair in parts[1].split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                labels[k] = v
        
        return labels

    def _record_point(self, name: str, value: float,
                     labels: Dict[str, str] = None):
        """Record a metric data point"""
        point = MetricPoint(
            timestamp=datetime.now().isoformat(),
            value=value,
            labels=labels or {}
        )
        
        self.data[name].append(point)

    def _format_prometheus_line(self, name: str, value: float,
                               labels: Dict[str, str] = None) -> str:
        """Format metric in Prometheus line format"""
        if not labels:
            return f"{name} {value}"
        
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f'{name}{{{label_str}}} {value}'

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _count_metrics_by_type(self) -> Dict[str, int]:
        """Count metrics by type"""
        counts = {}
        for metric in self.metrics.values():
            counts[metric.type] = counts.get(metric.type, 0) + 1
        return counts

    def _get_all_current_values(self) -> Dict[str, float]:
        """Get all current metric values"""
        values = {}
        for name in self.metrics:
            val = self.get_metric_value(name)
            if val is not None:
                values[name] = val
        return values

    def _load_metrics(self):
        """Load metrics from storage"""
        metrics_file = self.storage_path / "metrics_registry.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
                    for name, metric_data in data.items():
                        self.metrics[name] = Metric(**metric_data)
            except Exception as e:
                print(f"Error loading metrics: {e}")

    def _save_metrics(self):
        """Save metrics to storage"""
        try:
            metrics_file = self.storage_path / "metrics_registry.json"
            data = {name: asdict(m) for name, m in self.metrics.items()}
            with open(metrics_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving metrics: {e}")


# Global metrics collector instance
_metrics_collector = None

def get_metrics_collector(storage_path: str = "/tmp/monitoring/metrics") -> MetricsCollector:
    """Get or create global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(storage_path)
    return _metrics_collector
