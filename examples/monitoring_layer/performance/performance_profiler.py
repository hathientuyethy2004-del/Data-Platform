"""
Performance Profiler
CPU, memory, I/O, and latency profiling for data platform
"""

import json
import time
import tracemalloc
import os
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: str
    component: str
    operation: str
    
    # Timing metrics (ms)
    wall_time_ms: float
    cpu_time_ms: float
    io_wait_ms: float
    
    # Memory metrics (MB)
    memory_used_mb: float
    memory_peak_mb: float
    memory_allocated_mb: float
    memory_freed_mb: float
    
    # I/O metrics
    io_reads: int = 0
    io_writes: int = 0
    io_read_bytes: int = 0
    io_write_bytes: int = 0
    
    # Efficiency
    efficiency_score: float = 0.0  # 0-100
    bottleneck: str = ""  # cpu, memory, io


@dataclass
class ProfileSession:
    """Performance profiling session"""
    session_id: str
    component: str
    operation: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "running"
    metrics: List[PerformanceMetrics] = None
    duration_ms: float = 0.0


class PerformanceProfiler:
    """System for profiling component performance"""

    def __init__(self):
        """Initialize performance profiler"""
        self.storage_path = Path("monitoring_data/profiles")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.active_sessions: Dict[str, ProfileSession] = {}
        self.completed_sessions: Dict[str, ProfileSession] = {}
        
        self.metric_samples: Dict[str, List[PerformanceMetrics]] = defaultdict(list)
        self.lock = threading.Lock()
        
        # Get process info
        try:
            self.process = psutil.Process(os.getpid())
        except:
            self.process = None
        
        # Start memory tracking
        tracemalloc.start()

    def start_profiling(self, session_id: str, component: str,
                       operation: str) -> str:
        """Start a profiling session"""
        with self.lock:
            session = ProfileSession(
                session_id=session_id,
                component=component,
                operation=operation,
                start_time=datetime.now().isoformat(),
                metrics=[]
            )
            
            self.active_sessions[session_id] = session
            return session_id

    def record_sample(self, session_id: str, wall_time_ms: float,
                     cpu_time_ms: float = 0.0, io_wait_ms: float = 0.0) -> bool:
        """Record a performance sample"""
        if session_id not in self.active_sessions:
            return False
        
        # Get memory stats
        memory_used_mb = 0.0
        memory_peak_mb = 0.0
        memory_allocated_mb = 0.0
        
        if self.process:
            try:
                mem_info = self.process.memory_info()
                memory_used_mb = mem_info.rss / (1024 * 1024)
            except:
                pass
        
        current, peak = tracemalloc.get_traced_memory()
        memory_allocated_mb = current / (1024 * 1024)
        memory_peak_mb = peak / (1024 * 1024)
        
        # Get I/O stats
        io_reads = 0
        io_writes = 0
        
        if self.process:
            try:
                io_counters = self.process.io_counters()
                io_reads = io_counters.read_count
                io_writes = io_counters.write_count
            except:
                pass
        
        # Calculate efficiency score
        efficiency = self._calculate_efficiency(
            wall_time_ms, cpu_time_ms, io_wait_ms,
            memory_used_mb, memory_peak_mb
        )
        
        # Identify bottleneck
        bottleneck = self._identify_bottleneck(
            wall_time_ms, cpu_time_ms, io_wait_ms
        )
        
        session = self.active_sessions[session_id]
        metric = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            component=session.component,
            operation=session.operation,
            wall_time_ms=wall_time_ms,
            cpu_time_ms=cpu_time_ms,
            io_wait_ms=io_wait_ms,
            memory_used_mb=memory_used_mb,
            memory_peak_mb=memory_peak_mb,
            memory_allocated_mb=memory_allocated_mb,
            memory_freed_mb=max(0, memory_peak_mb - memory_used_mb),
            efficiency_score=efficiency,
            bottleneck=bottleneck
        )
        
        with self.lock:
            session.metrics.append(metric)
            self.metric_samples[session.component].append(metric)
        
        return True

    def end_profiling(self, session_id: str, status: str = "completed") -> Optional[ProfileSession]:
        """End a profiling session"""
        if session_id not in self.active_sessions:
            return None
        
        with self.lock:
            session = self.active_sessions.pop(session_id)
            session.end_time = datetime.now().isoformat()
            session.status = status
            
            if session.metrics:
                session.duration_ms = sum(m.wall_time_ms for m in session.metrics)
            
            self.completed_sessions[session_id] = session
            self._save_session(session)
        
        return session

    def get_session_summary(self, session_id: str) -> Dict:
        """Get summary of a profiling session"""
        session = self.completed_sessions.get(session_id)
        if not session:
            return {}
        
        if not session.metrics:
            return {}
        
        metrics_list = session.metrics
        
        # Calculate statistics
        wall_times = [m.wall_time_ms for m in metrics_list]
        cpu_times = [m.cpu_time_ms for m in metrics_list]
        memory_used = [m.memory_used_mb for m in metrics_list]
        memory_peak = [m.memory_peak_mb for m in metrics_list]
        efficiency_scores = [m.efficiency_score for m in metrics_list]
        
        def stats(values):
            if not values:
                return {}
            return {
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "median": sorted(values)[len(values) // 2]
            }
        
        return {
            "session_id": session_id,
            "component": session.component,
            "operation": session.operation,
            "status": session.status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "total_duration_ms": session.duration_ms,
            "sample_count": len(metrics_list),
            
            "wall_time_stats": stats(wall_times),
            "cpu_time_stats": stats(cpu_times),
            "memory_used_stats": stats(memory_used),
            "memory_peak_stats": stats(memory_peak),
            
            "avg_efficiency": sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0.0,
            "bottleneck_summary": self._get_bottleneck_summary(metrics_list),
            "recommendations": self._get_optimization_recommendations(metrics_list)
        }

    def get_component_profile(self, component: str, hours: int = 24) -> Dict:
        """Get performance profile for a component"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_metrics = [
            m for m in self.metric_samples[component]
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"component": component, "data_available": False}
        
        wall_times = [m.wall_time_ms for m in recent_metrics]
        memory_used = [m.memory_used_mb for m in recent_metrics]
        efficiency = [m.efficiency_score for m in recent_metrics]
        
        def percentile(values, p):
            if not values:
                return 0
            sorted_vals = sorted(values)
            index = int(len(sorted_vals) * p / 100)
            return sorted_vals[min(index, len(sorted_vals) - 1)]
        
        return {
            "component": component,
            "period_hours": hours,
            "sample_count": len(recent_metrics),
            "data_available": True,
            
            "latency_statistics": {
                "p50": percentile(wall_times, 50),
                "p95": percentile(wall_times, 95),
                "p99": percentile(wall_times, 99),
                "p99_9": percentile(wall_times, 99.9),
                "mean": sum(wall_times) / len(wall_times),
                "max": max(wall_times)
            },
            
            "memory_statistics": {
                "mean": sum(memory_used) / len(memory_used),
                "peak": max(memory_used),
                "min": min(memory_used)
            },
            
            "efficiency": {
                "mean": sum(efficiency) / len(efficiency),
                "min": min(efficiency),
                "max": max(efficiency)
            },
            
            "trends": self._analyze_trends(recent_metrics),
            "health": self._assess_component_health(recent_metrics)
        }

    def export_profile_report(self, output_path: str) -> bool:
        """Export performance profile report"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "total_sessions": len(self.completed_sessions),
                "sessions": {},
                "component_profiles": {}
            }
            
            # Add session summaries
            for session_id, session in self.completed_sessions.items():
                report["sessions"][session_id] = self.get_session_summary(session_id)
            
            # Add component profiles
            for component in self.metric_samples.keys():
                report["component_profiles"][component] = self.get_component_profile(component)
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting profile report: {e}")
            return False

    def _calculate_efficiency(self, wall_time: float, cpu_time: float,
                             io_wait: float, memory_used: float,
                             memory_peak: float) -> float:
        """Calculate efficiency score (0-100)"""
        if wall_time == 0:
            return 0.0
        
        cpu_efficiency = min(100, (cpu_time / wall_time) * 100) if wall_time > 0 else 0
        memory_efficiency = max(0, 100 - (memory_used / max(1, memory_peak)) * 50)
        io_efficiency = min(100, 100 - (io_wait / wall_time) * 50) if wall_time > 0 else 100
        
        # Weighted average
        efficiency = (cpu_efficiency * 0.4 + memory_efficiency * 0.3 + io_efficiency * 0.3)
        return min(100, max(0, efficiency))

    def _identify_bottleneck(self, wall_time: float, cpu_time: float,
                            io_wait: float) -> str:
        """Identify the main performance bottleneck"""
        if wall_time == 0:
            return "unknown"
        
        cpu_ratio = cpu_time / wall_time
        io_ratio = io_wait / wall_time
        
        if cpu_ratio > 0.6:
            return "cpu"
        elif io_ratio > 0.4:
            return "io"
        else:
            return "other"

    def _get_bottleneck_summary(self, metrics: List[PerformanceMetrics]) -> Dict:
        """Summarize bottlenecks across metrics"""
        bottleneck_counts = defaultdict(int)
        for m in metrics:
            bottleneck_counts[m.bottleneck] += 1
        
        return dict(bottleneck_counts)

    def _get_optimization_recommendations(self, metrics: List[PerformanceMetrics]) -> List[str]:
        """Get optimization recommendations based on metrics"""
        recommendations = []
        
        if not metrics:
            return recommendations
        
        # Memory optimization
        peak_memory = max(m.memory_peak_mb for m in metrics)
        avg_memory = sum(m.memory_used_mb for m in metrics) / len(metrics)
        
        if peak_memory > avg_memory * 1.5:
            recommendations.append("Consider implementing memory pooling or object reuse")
        
        # CPU optimization
        bottleneck_summary = self._get_bottleneck_summary(metrics)
        if bottleneck_summary.get("cpu", 0) > len(metrics) * 0.5:
            recommendations.append("High CPU usage detected - consider parallelization")
        
        # I/O optimization
        if bottleneck_summary.get("io", 0) > len(metrics) * 0.5:
            recommendations.append("High I/O wait time - consider caching or batch operations")
        
        # Efficiency optimization
        avg_efficiency = sum(m.efficiency_score for m in metrics) / len(metrics)
        if avg_efficiency < 60:
            recommendations.append("Overall efficiency is low - review algorithm efficiency")
        
        return recommendations

    def _analyze_trends(self, metrics: List[PerformanceMetrics]) -> Dict:
        """Analyze performance trends"""
        if len(metrics) < 2:
            return {"trend": "insufficient_data"}
        
        recent_half = metrics[len(metrics)//2:]
        early_half = metrics[:len(metrics)//2]
        
        recent_avg = sum(m.wall_time_ms for m in recent_half) / len(recent_half)
        early_avg = sum(m.wall_time_ms for m in early_half) / len(early_half)
        
        if early_avg == 0:
            change_pct = 0
        else:
            change_pct = ((recent_avg - early_avg) / early_avg) * 100
        
        trend = "improving" if change_pct < -5 else ("degrading" if change_pct > 5 else "stable")
        
        return {
            "trend": trend,
            "change_percent": change_pct,
            "recent_avg_ms": recent_avg,
            "early_avg_ms": early_avg
        }

    def _assess_component_health(self, metrics: List[PerformanceMetrics]) -> str:
        """Assess component health status"""
        if not metrics:
            return "unknown"
        
        avg_efficiency = sum(m.efficiency_score for m in metrics) / len(metrics)
        
        if avg_efficiency >= 80:
            return "healthy"
        elif avg_efficiency >= 60:
            return "degraded"
        else:
            return "unhealthy"

    def _save_session(self, session: ProfileSession):
        """Save session to file"""
        try:
            session_file = self.storage_path / f"{session.session_id}.json"
            with open(session_file, 'w') as f:
                data = {
                    "session": asdict(session),
                    "metrics": [asdict(m) for m in (session.metrics or [])]
                }
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving session: {e}")


# Global profiler instance
_profiler = None

def get_performance_profiler() -> PerformanceProfiler:
    """Get or create global performance profiler"""
    global _profiler
    if _profiler is None:
        _profiler = PerformanceProfiler()
    return _profiler
