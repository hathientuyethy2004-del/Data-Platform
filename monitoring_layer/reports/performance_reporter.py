"""
Performance Reports
Comprehensive performance analysis and reporting
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import threading


@dataclass
class PerformanceSummary:
    """Daily performance summary"""
    date: str
    
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    throughput_records_per_second: float = 0.0
    total_records_processed: int = 0
    
    error_rate: float = 0.0
    total_errors: int = 0
    
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    
    availability_percent: float = 100.0
    uptime_minutes: int = 0


@dataclass
class TrendAnalysis:
    """Trend analysis over time"""
    metric: str
    period_days: int
    
    current_value: float = 0.0
    previous_value: float = 0.0
    change_percent: float = 0.0
    
    trend_direction: str = "stable"  # improving, degrading, stable
    
    min_value: float = 0.0
    max_value: float = 0.0
    avg_value: float = 0.0
    std_dev: float = 0.0


@dataclass
class ComponentPerformance:
    """Performance metrics for a component"""
    component: str
    timestamp: str
    
    latency_ms: float = 0.0
    throughput: float = 0.0
    error_rate: float = 0.0
    
    resource_utilization: float = 0.0  # 0-100
    efficiency_score: float = 0.0  # 0-100
    
    health_status: str = "healthy"  # healthy, degraded, unhealthy
    

class PerformanceReporter:
    """Performance reporting and analysis"""

    def __init__(self):
        """Initialize performance reporter"""
        self.storage_path = Path("monitoring_data/reports")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.daily_summaries: Dict[str, PerformanceSummary] = {}
        self.trend_analyses: Dict[str, List[TrendAnalysis]] = {}
        self.component_metrics: Dict[str, List[ComponentPerformance]] = {}
        
        self.lock = threading.Lock()
        self._load_reports()

    def record_component_performance(self, component: str,
                                    latency_ms: float = 0.0,
                                    throughput: float = 0.0,
                                    error_rate: float = 0.0,
                                    resource_utilization: float = 0.0,
                                    efficiency_score: float = 0.0) -> bool:
        """Record component performance metrics"""
        
        # Determine health status
        if efficiency_score >= 80:
            health_status = "healthy"
        elif efficiency_score >= 60:
            health_status = "degraded"
        else:
            health_status = "unhealthy"
        
        perf = ComponentPerformance(
            component=component,
            timestamp=datetime.now().isoformat(),
            latency_ms=latency_ms,
            throughput=throughput,
            error_rate=error_rate,
            resource_utilization=resource_utilization,
            efficiency_score=efficiency_score,
            health_status=health_status
        )
        
        with self.lock:
            if component not in self.component_metrics:
                self.component_metrics[component] = []
            
            self.component_metrics[component].append(perf)
            
            # Keep only last 1000 records per component
            if len(self.component_metrics[component]) > 1000:
                self.component_metrics[component] = self.component_metrics[component][-1000:]
            
            self._save_reports()
        
        return True

    def generate_daily_summary(self, date: str = None) -> PerformanceSummary:
        """Generate daily performance summary"""
        if date is None:
            date = datetime.now().date().isoformat()
        
        # Get metrics for the day
        target_date = datetime.fromisoformat(date)
        start_of_day = target_date.replace(hour=0, minute=0, second=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        latencies = []
        errors = 0
        total_records = 0
        uptime = 1440  # Minutes in a day
        
        cpu_usage = 0.0
        memory_usage = 0.0
        metric_count = 0
        
        for component_metrics in self.component_metrics.values():
            for perf in component_metrics:
                perf_time = datetime.fromisoformat(perf.timestamp)
                
                if start_of_day <= perf_time < end_of_day:
                    if perf.latency_ms > 0:
                        latencies.append(perf.latency_ms)
                    
                    errors += perf.error_rate
                    total_records += int(perf.throughput)
                    
                    if perf.health_status == "unhealthy":
                        uptime -= 1  # Reduce by 1 minute per unhealthy reading
                    
                    cpu_usage += perf.resource_utilization
                    metric_count += 1
        
        # Calculate statistics
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
        
        throughput = total_records / 1440 if total_records > 0 else 0  # Records per minute
        avg_cpu = cpu_usage / metric_count if metric_count > 0 else 0
        
        availability = max(0, (uptime / 1440) * 100)
        
        summary = PerformanceSummary(
            date=date,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            throughput_records_per_second=throughput,
            total_records_processed=total_records,
            error_rate=errors / metric_count if metric_count > 0 else 0,
            total_errors=int(errors),
            cpu_usage_percent=avg_cpu,
            memory_usage_percent=avg_cpu * 0.7,  # Estimate
            availability_percent=availability,
            uptime_minutes=uptime
        )
        
        with self.lock:
            self.daily_summaries[date] = summary
            self._save_reports()
        
        return summary

    def analyze_trends(self, metric: str, days: int = 30) -> TrendAnalysis:
        """Analyze trends for a metric"""
        cutoff = datetime.now() - timedelta(days=days)
        
        values = []
        
        for component_metrics in self.component_metrics.values():
            for perf in component_metrics:
                perf_time = datetime.fromisoformat(perf.timestamp)
                if perf_time < cutoff:
                    continue
                
                # Extract metric value
                if metric == "latency":
                    values.append(perf.latency_ms)
                elif metric == "throughput":
                    values.append(perf.throughput)
                elif metric == "error_rate":
                    values.append(perf.error_rate)
                elif metric == "resource_utilization":
                    values.append(perf.resource_utilization)
                elif metric == "efficiency":
                    values.append(perf.efficiency_score)
        
        if not values:
            return TrendAnalysis(metric=metric, period_days=days)
        
        # Calculate statistics
        avg_value = sum(values) / len(values)
        min_value = min(values)
        max_value = max(values)
        variance = sum((v - avg_value) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        
        # Trend direction
        mid = len(values) // 2
        early_avg = sum(values[:mid]) / mid if mid > 0 else avg_value
        recent_avg = sum(values[mid:]) / (len(values) - mid) if len(values) > mid else avg_value
        
        if metric in ["error_rate"]:  # Lower is better
            if recent_avg < early_avg:
                trend_direction = "improving"
            elif recent_avg > early_avg:
                trend_direction = "degrading"
            else:
                trend_direction = "stable"
        else:  # Higher is better for throughput, efficiency
            if recent_avg > early_avg:
                trend_direction = "improving"
            elif recent_avg < early_avg:
                trend_direction = "degrading"
            else:
                trend_direction = "stable"
        
        current_value = values[-1] if values else 0
        previous_value = values[-2] if len(values) > 1 else current_value
        change_percent = ((current_value - previous_value) / previous_value * 100) if previous_value != 0 else 0
        
        trend = TrendAnalysis(
            metric=metric,
            period_days=days,
            current_value=current_value,
            previous_value=previous_value,
            change_percent=change_percent,
            trend_direction=trend_direction,
            min_value=min_value,
            max_value=max_value,
            avg_value=avg_value,
            std_dev=std_dev
        )
        
        with self.lock:
            if metric not in self.trend_analyses:
                self.trend_analyses[metric] = []
            self.trend_analyses[metric].append(trend)
        
        return trend

    def get_weekly_report(self) -> Dict:
        """Generate weekly performance report"""
        last_7_days = [(datetime.now() - timedelta(days=i)).date().isoformat() 
                       for i in range(7, 0, -1)]
        
        summaries = []
        for date in last_7_days:
            if date in self.daily_summaries:
                summaries.append(self.daily_summaries[date])
            else:
                summaries.append(self.generate_daily_summary(date))
        
        # Calculate weekly aggregate
        avg_latency = sum(s.avg_latency_ms for s in summaries) / len(summaries) if summaries else 0
        avg_throughput = sum(s.throughput_records_per_second for s in summaries) / len(summaries) if summaries else 0
        avg_error_rate = sum(s.error_rate for s in summaries) / len(summaries) if summaries else 0
        avg_availability = sum(s.availability_percent for s in summaries) / len(summaries) if summaries else 100
        
        return {
            "period": "weekly",
            "start_date": last_7_days[0],
            "end_date": last_7_days[-1],
            "daily_summaries": [asdict(s) for s in summaries],
            "weekly_aggregate": {
                "avg_latency_ms": avg_latency,
                "avg_throughput": avg_throughput,
                "avg_error_rate": avg_error_rate,
                "avg_availability": avg_availability
            }
        }

    def get_monthly_report(self) -> Dict:
        """Generate monthly performance report"""
        last_30_days = [(datetime.now() - timedelta(days=i)).date().isoformat() 
                        for i in range(30, 0, -1)]
        
        summaries = []
        for date in last_30_days:
            if date in self.daily_summaries:
                summaries.append(self.daily_summaries[date])
        
        if not summaries:
            return {"period": "monthly", "data_available": False}
        
        # Calculate monthly aggregate
        avg_latency = sum(s.avg_latency_ms for s in summaries) / len(summaries)
        avg_throughput = sum(s.throughput_records_per_second for s in summaries) / len(summaries)
        avg_error_rate = sum(s.error_rate for s in summaries) / len(summaries)
        avg_availability = sum(s.availability_percent for s in summaries) / len(summaries)
        
        # Top issues
        worst_days = sorted(summaries, key=lambda s: s.error_rate, reverse=True)[:3]
        
        return {
            "period": "monthly",
            "start_date": last_30_days[0],
            "end_date": last_30_days[-1],
            "days_with_data": len(summaries),
            "monthly_aggregate": {
                "avg_latency_ms": avg_latency,
                "avg_throughput": avg_throughput,
                "avg_error_rate": avg_error_rate,
                "avg_availability": avg_availability,
                "total_records_processed": sum(s.total_records_processed for s in summaries),
                "total_errors": sum(s.total_errors for s in summaries)
            },
            "worst_performing_days": [asdict(s) for s in worst_days]
        }

    def get_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Analyze recent trends
        latency_trend = self.analyze_trends("latency", days=7)
        error_trend = self.analyze_trends("error_rate", days=7)
        efficiency_trend = self.analyze_trends("efficiency", days=7)
        
        # Latency recommendations
        if latency_trend.trend_direction == "degrading":
            recommendations.append("Latency is degrading - consider scaling up resources")
        elif latency_trend.current_value > 1000:  # > 1 second
            recommendations.append("High latency detected - optimize queries and indexing")
        
        # Error rate recommendations
        if error_trend.trend_direction == "degrading":
            recommendations.append("Error rate increasing - review recent changes")
        elif error_trend.current_value > 0.01:  # > 1%
            recommendations.append("Error rate above 1% - investigate root causes")
        
        # Efficiency recommendations
        if efficiency_trend.trend_direction == "degrading":
            recommendations.append("Efficiency declining - check resource utilization")
        elif efficiency_trend.current_value < 70:
            recommendations.append("Overall efficiency below 70% - consider optimization")
        
        return recommendations

    def export_performance_report(self, output_path: str, period: str = "weekly") -> bool:
        """Export performance report"""
        try:
            if period == "weekly":
                report = self.get_weekly_report()
            else:
                report = self.get_monthly_report()
            
            report["recommendations"] = self.get_recommendations()
            report["generated_at"] = datetime.now().isoformat()
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting performance report: {e}")
            return False

    def export_component_report(self, component: str, output_path: str, days: int = 30) -> bool:
        """Export component-specific report"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            if component not in self.component_metrics:
                return False
            
            metrics = [m for m in self.component_metrics[component]
                      if datetime.fromisoformat(m.timestamp) >= cutoff]
            
            if not metrics:
                return False
            
            # Calculate statistics
            latencies = [m.latency_ms for m in metrics if m.latency_ms > 0]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            
            report = {
                "component": component,
                "period_days": days,
                "timestamp": datetime.now().isoformat(),
                "statistics": {
                    "avg_latency_ms": avg_latency,
                    "avg_throughput": sum(m.throughput for m in metrics) / len(metrics),
                    "avg_error_rate": sum(m.error_rate for m in metrics) / len(metrics),
                    "avg_efficiency_score": sum(m.efficiency_score for m in metrics) / len(metrics),
                    "health_uptime_percent": (len([m for m in metrics if m.health_status == "healthy"]) / len(metrics) * 100)
                },
                "recent_metrics": [asdict(m) for m in metrics[-100:]]
            }
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting component report: {e}")
            return False

    def _load_reports(self):
        """Load stored reports"""
        summaries_file = self.storage_path / "daily_summaries.json"
        if summaries_file.exists():
            try:
                with open(summaries_file, 'r') as f:
                    data = json.load(f)
                    self.daily_summaries = {k: PerformanceSummary(**v) for k, v in data.items()}
            except Exception as e:
                print(f"Error loading daily summaries: {e}")

    def _save_reports(self):
        """Save reports to file"""
        try:
            summaries_file = self.storage_path / "daily_summaries.json"
            with open(summaries_file, 'w') as f:
                data = {k: asdict(v) for k, v in self.daily_summaries.items()}
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving reports: {e}")


# Global performance reporter instance
_performance_reporter = None

def get_performance_reporter() -> PerformanceReporter:
    """Get or create global performance reporter"""
    global _performance_reporter
    if _performance_reporter is None:
        _performance_reporter = PerformanceReporter()
    return _performance_reporter
