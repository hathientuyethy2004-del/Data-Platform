"""
Cost Tracker
Track computational costs and correlate with performance metrics
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading


class ResourceType(Enum):
    """Resource types for cost calculation"""
    CPU_HOURS = "cpu_hours"
    GPU_HOURS = "gpu_hours"
    MEMORY_MB_HOURS = "memory_mb_hours"
    STORAGE_GB_MONTHS = "storage_gb_months"
    DATA_GB_TRANSFERRED = "data_gb_transferred"
    EXECUTION_MINUTES = "execution_minutes"


@dataclass
class CostProfile:
    """Cost configuration for resources"""
    cpu_cost_per_hour: float = 0.05  # $ per CPU hour
    gpu_cost_per_hour: float = 0.30  # $ per GPU hour
    memory_cost_per_gb_month: float = 0.01  # $ per GB per month
    storage_cost_per_gb_month: float = 0.023  # $ per GB per month
    data_transfer_cost_per_gb: float = 0.02  # $ per GB
    execution_cost_base: float = 0.001  # $ per minute


@dataclass
class ResourceUsage:
    """Resource usage record"""
    timestamp: str
    component: str
    operation: str
    
    cpu_hours: float = 0.0
    gpu_hours: float = 0.0
    memory_mb_hours: float = 0.0
    storage_gb: float = 0.0
    data_transferred_gb: float = 0.0
    execution_minutes: float = 0.0
    
    total_cost: float = 0.0


@dataclass
class CostReport:
    """Cost analysis report"""
    timestamp: str
    period_start: str
    period_end: str
    
    total_cost: float = 0.0
    by_component: Dict[str, float] = None
    by_resource_type: Dict[str, float] = None
    by_operation: Dict[str, float] = None
    
    cost_per_records: float = 0.0  # Cost per million records
    cost_per_gb_data: float = 0.0  # Cost per GB of data
    efficiency_score: float = 0.0


class CostTracker:
    """Computational cost tracking and analysis"""

    def __init__(self, cost_profile: CostProfile = None):
        """Initialize cost tracker"""
        self.storage_path = Path("monitoring_data/costs")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.cost_profile = cost_profile or CostProfile()
        
        self.usage_records: List[ResourceUsage] = []
        self.component_costs: Dict[str, float] = {}
        self.resource_costs: Dict[str, float] = {}
        
        self.lock = threading.Lock()
        self._load_usage_records()

    def record_usage(self, component: str, operation: str,
                     cpu_hours: float = 0.0, gpu_hours: float = 0.0,
                     memory_mb_hours: float = 0.0, storage_gb: float = 0.0,
                     data_transferred_gb: float = 0.0, execution_minutes: float = 0.0) -> str:
        """Record resource usage"""
        
        # Calculate costs
        cpu_cost = cpu_hours * self.cost_profile.cpu_cost_per_hour
        gpu_cost = gpu_hours * self.cost_profile.gpu_cost_per_hour
        memory_cost = memory_mb_hours * self.cost_profile.memory_cost_per_gb_month / (24 * 30)  # Convert to hourly
        storage_cost = storage_gb * self.cost_profile.storage_cost_per_gb_month / (24 * 30)
        transfer_cost = data_transferred_gb * self.cost_profile.data_transfer_cost_per_gb
        execution_cost = execution_minutes * self.cost_profile.execution_cost_base
        
        total_cost = cpu_cost + gpu_cost + memory_cost + storage_cost + transfer_cost + execution_cost
        
        usage = ResourceUsage(
            timestamp=datetime.now().isoformat(),
            component=component,
            operation=operation,
            cpu_hours=cpu_hours,
            gpu_hours=gpu_hours,
            memory_mb_hours=memory_mb_hours,
            storage_gb=storage_gb,
            data_transferred_gb=data_transferred_gb,
            execution_minutes=execution_minutes,
            total_cost=total_cost
        )
        
        with self.lock:
            self.usage_records.append(usage)
            
            # Update component costs
            if component not in self.component_costs:
                self.component_costs[component] = 0.0
            self.component_costs[component] += total_cost
            
            # Update resource costs
            self.resource_costs[ResourceType.CPU_HOURS.value] = \
                self.resource_costs.get(ResourceType.CPU_HOURS.value, 0) + cpu_cost
            self.resource_costs[ResourceType.GPU_HOURS.value] = \
                self.resource_costs.get(ResourceType.GPU_HOURS.value, 0) + gpu_cost
            self.resource_costs[ResourceType.MEMORY_MB_HOURS.value] = \
                self.resource_costs.get(ResourceType.MEMORY_MB_HOURS.value, 0) + memory_cost
            self.resource_costs[ResourceType.STORAGE_GB_MONTHS.value] = \
                self.resource_costs.get(ResourceType.STORAGE_GB_MONTHS.value, 0) + storage_cost
            self.resource_costs[ResourceType.DATA_GB_TRANSFERRED.value] = \
                self.resource_costs.get(ResourceType.DATA_GB_TRANSFERRED.value, 0) + transfer_cost
            self.resource_costs[ResourceType.EXECUTION_MINUTES.value] = \
                self.resource_costs.get(ResourceType.EXECUTION_MINUTES.value, 0) + execution_cost
            
            self._save_usage_records()
        
        return f"{component}_{operation}_{int(time.time())}"

    def get_cost_by_component(self, days: int = 30) -> Dict[str, float]:
        """Get cost breakdown by component"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        costs = {}
        for usage in self.usage_records:
            usage_time = datetime.fromisoformat(usage.timestamp)
            if usage_time < cutoff_time:
                continue
            
            if usage.component not in costs:
                costs[usage.component] = 0.0
            costs[usage.component] += usage.total_cost
        
        return costs

    def get_cost_by_operation(self, component: str = None, days: int = 30) -> Dict[str, float]:
        """Get cost breakdown by operation"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        costs = {}
        for usage in self.usage_records:
            usage_time = datetime.fromisoformat(usage.timestamp)
            if usage_time < cutoff_time:
                continue
            
            if component and usage.component != component:
                continue
            
            key = f"{usage.component}:{usage.operation}"
            if key not in costs:
                costs[key] = 0.0
            costs[key] += usage.total_cost
        
        return costs

    def get_cost_by_resource(self, days: int = 30) -> Dict[str, float]:
        """Get cost breakdown by resource type"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        costs = {
            ResourceType.CPU_HOURS.value: 0.0,
            ResourceType.GPU_HOURS.value: 0.0,
            ResourceType.MEMORY_MB_HOURS.value: 0.0,
            ResourceType.STORAGE_GB_MONTHS.value: 0.0,
            ResourceType.DATA_GB_TRANSFERRED.value: 0.0,
            ResourceType.EXECUTION_MINUTES.value: 0.0
        }
        
        for usage in self.usage_records:
            usage_time = datetime.fromisoformat(usage.timestamp)
            if usage_time < cutoff_time:
                continue
            
            costs[ResourceType.CPU_HOURS.value] += usage.cpu_hours * self.cost_profile.cpu_cost_per_hour
            costs[ResourceType.GPU_HOURS.value] += usage.gpu_hours * self.cost_profile.gpu_cost_per_hour
            costs[ResourceType.MEMORY_MB_HOURS.value] += usage.memory_mb_hours * self.cost_profile.memory_cost_per_gb_month / (24 * 30)
            costs[ResourceType.STORAGE_GB_MONTHS.value] += usage.storage_gb * self.cost_profile.storage_cost_per_gb_month / (24 * 30)
            costs[ResourceType.DATA_GB_TRANSFERRED.value] += usage.data_transferred_gb * self.cost_profile.data_transfer_cost_per_gb
            costs[ResourceType.EXECUTION_MINUTES.value] += usage.execution_minutes * self.cost_profile.execution_cost_base
        
        return costs

    def get_total_cost(self, days: int = 30) -> float:
        """Get total cost for period"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        total = 0.0
        for usage in self.usage_records:
            usage_time = datetime.fromisoformat(usage.timestamp)
            if usage_time >= cutoff_time:
                total += usage.total_cost
        
        return total

    def get_cost_trends(self, days: int = 30) -> Dict:
        """Get cost trends over time"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        daily_costs = {}
        for usage in self.usage_records:
            usage_time = datetime.fromisoformat(usage.timestamp)
            if usage_time < cutoff_time:
                continue
            
            day_key = usage_time.date().isoformat()
            if day_key not in daily_costs:
                daily_costs[day_key] = 0.0
            daily_costs[day_key] += usage.total_cost
        
        dates = sorted(daily_costs.keys())
        costs = [daily_costs[d] for d in dates]
        
        # Calculate trend
        if len(costs) >= 2:
            avg_early = sum(costs[:len(costs)//2]) / (len(costs)//2)
            avg_recent = sum(costs[len(costs)//2:]) / (len(costs) - len(costs)//2)
            trend_direction = "increasing" if avg_recent > avg_early else "decreasing"
            change_percent = ((avg_recent - avg_early) / avg_early * 100) if avg_early > 0 else 0
        else:
            trend_direction = "insufficient_data"
            change_percent = 0
        
        return {
            "period_days": days,
            "dates": dates,
            "daily_costs": costs,
            "total_cost": sum(costs),
            "average_daily": sum(costs) / len(costs) if costs else 0,
            "trend_direction": trend_direction,
            "change_percent": change_percent
        }

    def analyze_cost_efficiency(self, component: str,
                               records_processed: int = 0,
                               data_volume_gb: float = 0.0,
                               days: int = 30) -> Dict:
        """Analyze cost efficiency"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        component_usages = [
            u for u in self.usage_records
            if u.component == component and datetime.fromisoformat(u.timestamp) >= cutoff_time
        ]
        
        if not component_usages:
            return {"component": component, "data_available": False}
        
        total_cost = sum(u.total_cost for u in component_usages)
        
        metrics = {
            "component": component,
            "period_days": days,
            "total_cost": total_cost,
            "usage_count": len(component_usages),
            "average_cost_per_operation": total_cost / len(component_usages) if component_usages else 0,
            "data_available": True
        }
        
        # Cost per records
        if records_processed > 0:
            metrics["cost_per_million_records"] = (total_cost / records_processed) * 1_000_000
        
        # Cost per data
        if data_volume_gb > 0:
            metrics["cost_per_gb"] = total_cost / data_volume_gb
        
        # Resource breakdown
        total_cpu = sum(u.cpu_hours for u in component_usages)
        total_memory = sum(u.memory_mb_hours for u in component_usages)
        total_execution = sum(u.execution_minutes for u in component_usages)
        
        metrics["dominant_resource"] = max(
            ("cpu", total_cpu),
            ("memory", total_memory),
            ("execution", total_execution),
            key=lambda x: x[1]
        )[0]
        
        return metrics

    def generate_cost_report(self, days: int = 30,
                           records_processed: int = 0,
                           data_volume_gb: float = 0.0) -> CostReport:
        """Generate comprehensive cost report"""
        period_start = (datetime.now() - timedelta(days=days)).isoformat()
        period_end = datetime.now().isoformat()
        
        by_component = self.get_cost_by_component(days)
        by_resource = self.get_cost_by_resource(days)
        by_operation = self.get_cost_by_operation(days=days)
        
        total_cost = sum(by_component.values())
        
        # Calculate efficiency metrics
        cost_per_records = 0.0
        if records_processed > 0:
            cost_per_records = (total_cost / records_processed) * 1_000_000
        
        cost_per_gb = 0.0
        if data_volume_gb > 0:
            cost_per_gb = total_cost / data_volume_gb
        
        # Simple efficiency score (inverse of cost per records)
        efficiency_score = 100 / (cost_per_records + 1) if cost_per_records > 0 else 100
        
        report = CostReport(
            timestamp=datetime.now().isoformat(),
            period_start=period_start,
            period_end=period_end,
            total_cost=total_cost,
            by_component=by_component,
            by_resource_type=by_resource,
            by_operation=by_operation,
            cost_per_records=cost_per_records,
            cost_per_gb_data=cost_per_gb,
            efficiency_score=min(100, efficiency_score)
        )
        
        return report

    def export_cost_report(self, output_path: str, days: int = 30) -> bool:
        """Export cost report"""
        try:
            report = self.generate_cost_report(days=days)
            
            with open(output_path, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting cost report: {e}")
            return False

    def _load_usage_records(self):
        """Load usage records from file"""
        usage_file = self.storage_path / "usage_records.json"
        if not usage_file.exists():
            return
        
        try:
            with open(usage_file, 'r') as f:
                data = json.load(f)
                self.usage_records = [ResourceUsage(**record) for record in data]
        except Exception as e:
            print(f"Error loading usage records: {e}")

    def _save_usage_records(self):
        """Save usage records to file"""
        try:
            usage_file = self.storage_path / "usage_records.json"
            with open(usage_file, 'w') as f:
                json.dump([asdict(r) for r in self.usage_records], f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving usage records: {e}")


# Global cost tracker instance
_cost_tracker = None

def get_cost_tracker(cost_profile: CostProfile = None) -> CostTracker:
    """Get or create global cost tracker"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker(cost_profile)
    return _cost_tracker
