"""
Monitoring Module - Ingestion Layer
Theo dõi hiệu suất và sức khỏe của INGESTION LAYER
"""

import logging
import time
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collect và lưu trữ các metrics từ INGESTION LAYER
    - Throughput (messages/sec)
    - Latency (processing time)
    - Error rates
    - Consumer lag
    """

    def __init__(self, window_size: int = 300):  # 5 minutes window
        self.window_size = window_size
        self.metrics_queue = deque(maxlen=window_size)
        self.topic_metrics = defaultdict(lambda: deque(maxlen=window_size))
        
        # Cumulative metrics
        self.cumulative = {
            "total_messages": 0,
            "total_errors": 0,
            "total_processing_time": 0.0,
            "start_time": datetime.utcnow()
        }

    def record_message_processed(
        self,
        topic: str,
        processing_time_ms: float,
        success: bool = True,
        message_size_bytes: int = 0
    ):
        """Record một message được xử lý"""
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "topic": topic,
            "processing_time_ms": processing_time_ms,
            "success": success,
            "message_size_bytes": message_size_bytes
        }
        
        self.metrics_queue.append(metric)
        self.topic_metrics[topic].append(metric)
        
        self.cumulative["total_messages"] += 1
        if not success:
            self.cumulative["total_errors"] += 1
        self.cumulative["total_processing_time"] += processing_time_ms

    def get_throughput(self) -> Dict[str, float]:
        """
        Tính throughput (messages/sec)
        
        Returns:
            Dict với throughput by topic
        """
        if not self.metrics_queue:
            return {}

        if len(self.metrics_queue) < 2:
            return {}

        # Lấy first và last timestamp
        first_metric = self.metrics_queue[0]
        last_metric = self.metrics_queue[-1]
        
        first_time = datetime.fromisoformat(first_metric["timestamp"])
        last_time = datetime.fromisoformat(last_metric["timestamp"])
        
        time_diff = (last_time - first_time).total_seconds()
        if time_diff == 0:
            return {}

        # Overall throughput
        throughput = {
            "overall_msgs_per_sec": len(self.metrics_queue) / time_diff
        }

        # Per-topic throughput
        for topic, metrics in self.topic_metrics.items():
            if metrics:
                throughput[f"{topic}_msgs_per_sec"] = len(metrics) / time_diff

        return throughput

    def get_latency_stats(self) -> Dict[str, float]:
        """
        Tính latency statistics
        
        Returns:
            Dict với min/avg/max latency
        """
        if not self.metrics_queue:
            return {}

        processing_times = [m["processing_time_ms"] for m in self.metrics_queue]
        
        return {
            "latency_min_ms": min(processing_times),
            "latency_avg_ms": sum(processing_times) / len(processing_times),
            "latency_max_ms": max(processing_times),
            "latency_p95_ms": self._percentile(processing_times, 0.95),
            "latency_p99_ms": self._percentile(processing_times, 0.99)
        }

    def get_error_rate(self) -> Dict[str, float]:
        """Tính error rate"""
        if not self.metrics_queue:
            return {}

        total = len(self.metrics_queue)
        errors = sum(1 for m in self.metrics_queue if not m["success"])
        
        error_rate = (errors / total) * 100 if total > 0 else 0

        return {
            "total_metrics": total,
            "error_count": errors,
            "error_rate_percent": error_rate
        }

    def get_size_stats(self) -> Dict[str, int]:
        """Tính message size statistics"""
        if not self.metrics_queue:
            return {}

        sizes = [m["message_size_bytes"] for m in self.metrics_queue if m["message_size_bytes"] > 0]
        
        if not sizes:
            return {}

        total_bytes = sum(sizes)
        
        return {
            "total_size_bytes": total_bytes,
            "total_size_mb": total_bytes / (1024 * 1024),
            "avg_message_size_bytes": total_bytes / len(sizes),
            "min_message_size_bytes": min(sizes),
            "max_message_size_bytes": max(sizes)
        }

    def get_cumulative_metrics(self) -> Dict:
        """Lấy cumulative metrics"""
        uptime = datetime.utcnow() - self.cumulative["start_time"]
        uptime_seconds = uptime.total_seconds()
        
        avg_processing_time = (
            self.cumulative["total_processing_time"] / self.cumulative["total_messages"]
            if self.cumulative["total_messages"] > 0 else 0
        )
        
        overall_throughput = (
            self.cumulative["total_messages"] / uptime_seconds
            if uptime_seconds > 0 else 0
        )
        
        return {
            "start_time": self.cumulative["start_time"].isoformat(),
            "uptime_seconds": uptime_seconds,
            "total_messages_processed": self.cumulative["total_messages"],
            "total_errors": self.cumulative["total_errors"],
            "overall_throughput_msgs_per_sec": overall_throughput,
            "overall_avg_latency_ms": avg_processing_time
        }

    def get_full_metrics(self) -> Dict:
        """Lấy toàn bộ metrics"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "window_metrics": {
                "throughput": self.get_throughput(),
                "latency": self.get_latency_stats(),
                "errors": self.get_error_rate(),
                "message_size": self.get_size_stats()
            },
            "cumulative": self.get_cumulative_metrics()
        }
        return metrics

    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def print_metrics(self):
        """In ra metrics"""
        metrics = self.get_full_metrics()
        logger.info(
            f"\n📊 INGESTION LAYER METRICS:\n"
            f"Timestamp: {metrics['timestamp']}\n"
            f"\n⚡ Throughput (messages/sec):\n"
        )
        for key, value in metrics["window_metrics"]["throughput"].items():
            logger.info(f"  {key}: {value:.2f}")
        
        logger.info(f"\n⏱️  Latency (ms):\n")
        for key, value in metrics["window_metrics"]["latency"].items():
            logger.info(f"  {key}: {value:.2f}")
        
        logger.info(f"\n❌ Error Rate:\n")
        for key, value in metrics["window_metrics"]["errors"].items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.2f}%")
            else:
                logger.info(f"  {key}: {value}")
        
        logger.info(f"\n📦 Message Size (bytes):\n")
        for key, value in metrics["window_metrics"]["message_size"].items():
            if "mb" in key:
                logger.info(f"  {key}: {value:.2f}")
            else:
                logger.info(f"  {key}: {value}")
        
        logger.info(f"\n📈 Cumulative Metrics:\n")
        for key, value in metrics["cumulative"].items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.2f}")
            else:
                logger.info(f"  {key}: {value}")


class HealthCheck:
    """
    Health check cho INGESTION LAYER
    - Consumer lag
    - Processing latency
    - Error rate
    - Topic availability
    """

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alert_thresholds = {
            "error_rate_percent": 5.0,  # > 5% lỗi
            "latency_max_ms": 10000,    # > 10 second
            "consumer_lag": 100000      # > 100k messages
        }
        self.health_checks = []

    def check_error_rate(self) -> Dict[str, Any]:
        """Check error rate"""
        error_stats = self.metrics.get_error_rate()
        error_rate = error_stats.get("error_rate_percent", 0)
        
        threshold = self.alert_thresholds["error_rate_percent"]
        status = "healthy" if error_rate < threshold else "unhealthy"
        
        return {
            "check": "error_rate",
            "status": status,
            "value": error_rate,
            "threshold": threshold,
            "message": f"Error rate: {error_rate:.2f}%"
        }

    def check_latency(self) -> Dict[str, Any]:
        """Check latency"""
        latency_stats = self.metrics.get_latency_stats()
        latency_max = latency_stats.get("latency_max_ms", 0)
        latency_avg = latency_stats.get("latency_avg_ms", 0)
        
        threshold = self.alert_thresholds["latency_max_ms"]
        status = "healthy" if latency_max < threshold else "unhealthy"
        
        return {
            "check": "latency",
            "status": status,
            "value": latency_max,
            "average": latency_avg,
            "threshold": threshold,
            "message": f"Max latency: {latency_max:.0f}ms, Avg: {latency_avg:.0f}ms"
        }

    def check_throughput(self) -> Dict[str, Any]:
        """Check if system is processing messages"""
        throughput = self.metrics.get_throughput()
        overall_throughput = throughput.get("overall_msgs_per_sec", 0)
        
        # Alert if throughput is too low
        status = "healthy" if overall_throughput > 0 else "warning"
        
        return {
            "check": "throughput",
            "status": status,
            "value": overall_throughput,
            "message": f"Throughput: {overall_throughput:.2f} msgs/sec"
        }

    def perform_health_check(self) -> Dict[str, Any]:
        """Perform toàn bộ health check"""
        checks = [
            self.check_error_rate(),
            self.check_latency(),
            self.check_throughput()
        ]
        
        # Determine overall status
        unhealthy = sum(1 for c in checks if c["status"] == "unhealthy")
        warnings = sum(1 for c in checks if c["status"] == "warning")
        
        if unhealthy > 0:
            overall_status = "unhealthy"
        elif warnings > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status,
            "checks": checks,
            "summary": f"{len(checks)} checks, {unhealthy} unhealthy, {warnings} warnings"
        }

    def print_health_check(self):
        """In ra health check result"""
        health = self.perform_health_check()
        logger.info(
            f"\n❤️  HEALTH CHECK: {health['overall_status'].upper()}\n"
            f"Summary: {health['summary']}\n"
        )
        for check in health["checks"]:
            status_emoji = "✅" if check["status"] == "healthy" else "⚠️" if check["status"] == "warning" else "❌"
            logger.info(
                f"{status_emoji} {check['check'].upper()}: {check['message']}"
            )


if __name__ == "__main__":
    # Test monitoring
    collector = MetricsCollector()
    
    # Simulate some metrics
    for i in range(50):
        collector.record_message_processed(
            topic="topic_app_events",
            processing_time_ms=10 + (i % 5),
            success=i % 50 != 0,  # One error per 50 messages
            message_size_bytes=1024
        )
        time.sleep(0.01)
    
    # Print metrics
    collector.print_metrics()
    
    # Health check
    health = HealthCheck(collector)
    health.print_health_check()
