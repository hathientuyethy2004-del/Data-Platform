"""
Health Check Framework
Component health monitoring and status tracking
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading

from threading import Lock


class HealthStatus(Enum):
    """Health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Health check result"""
    check_name: str
    component: str
    status: str
    timestamp: str
    message: str = ""
    duration_ms: float = 0.0
    details: Dict = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class ComponentHealth:
    """Component health status"""
    component: str
    status: str
    last_check: str
    checks_passed: int = 0
    checks_failed: int = 0
    uptime_percent: float = 100.0
    last_error: str = ""
    details: Dict = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class HealthCheckManager:
    """Component health checking system"""

    def __init__(self, storage_path: str = "/tmp/monitoring/health"):
        """Initialize health check manager"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.checks: Dict[str, Callable] = {}
        self.results: Dict[str, List[HealthCheckResult]] = {}
        self.component_health: Dict[str, ComponentHealth] = {}
        self.lock = Lock()
        
        self._load_health_data()

    def register_check(self, component: str, check_name: str,
                      check_func: Callable) -> bool:
        """Register a health check"""
        key = f"{component}:{check_name}"
        
        if key in self.checks:
            return False
        
        self.checks[key] = (component, check_func)
        self.results[key] = []
        
        return True

    def run_check(self, component: str, check_name: str) -> Optional[HealthCheckResult]:
        """Run a single health check"""
        key = f"{component}:{check_name}"
        
        if key not in self.checks:
            return None
        
        _, check_func = self.checks[key]
        start_time = datetime.now()
        
        try:
            status, message, details = check_func()
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            result = HealthCheckResult(
                check_name=check_name,
                component=component,
                status=status,
                timestamp=datetime.now().isoformat(),
                message=message,
                duration_ms=duration,
                details=details
            )
            
            with self.lock:
                self.results[key].append(result)
                
                # Update component health
                self._update_component_health(component, result)
            
            return result
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            result = HealthCheckResult(
                check_name=check_name,
                component=component,
                status=HealthStatus.UNHEALTHY.value,
                timestamp=datetime.now().isoformat(),
                message=f"Check failed: {str(e)}",
                duration_ms=duration
            )
            
            with self.lock:
                self.results[key].append(result)
                self._update_component_health(component, result)
            
            return result

    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered checks"""
        results = {}
        
        for component, check_name in [tuple(k.split(":")) for k in self.checks]:
            result = self.run_check(component, check_name)
            if result:
                results[f"{component}:{check_name}"] = result
        
        return results

    def get_component_status(self, component: str) -> Optional[ComponentHealth]:
        """Get component health status"""
        return self.component_health.get(component)

    def get_all_components_status(self) -> Dict[str, ComponentHealth]:
        """Get all components' health status"""
        return dict(self.component_health)

    def get_check_history(self, component: str, check_name: str,
                         limit: int = 100) -> List[HealthCheckResult]:
        """Get history of check results"""
        key = f"{component}:{check_name}"
        
        if key not in self.results:
            return []
        
        results = self.results[key]
        return results[-limit:] if len(results) > limit else results

    def get_system_health(self) -> Dict:
        """Get overall system health"""
        components = list(self.component_health.values())
        
        if not components:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "timestamp": datetime.now().isoformat(),
                "components_checked": 0,
                "healthy_components": 0,
                "degraded_components": 0,
                "unhealthy_components": 0
            }
        
        healthy = sum(1 for c in components if c.status == HealthStatus.HEALTHY.value)
        degraded = sum(1 for c in components if c.status == HealthStatus.DEGRADED.value)
        unhealthy = sum(1 for c in components if c.status == HealthStatus.UNHEALTHY.value)
        
        # Determine overall status
        if unhealthy > 0:
            overall_status = HealthStatus.UNHEALTHY.value
        elif degraded > 0:
            overall_status = HealthStatus.DEGRADED.value
        else:
            overall_status = HealthStatus.HEALTHY.value
        
        # Calculate availability
        total_checks = sum(
            len(self.results.get(key, []))
            for key in self.checks
        )
        passed = sum(
            sum(1 for r in self.results.get(key, []) if r.status == HealthStatus.HEALTHY.value)
            for key in self.checks
        )
        
        availability = (passed / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components_checked": len(components),
            "healthy_components": healthy,
            "degraded_components": degraded,
            "unhealthy_components": unhealthy,
            "system_availability": availability,
            "components": {
                name: {
                    "status": health.status,
                    "uptime": health.uptime_percent,
                    "checks_passed": health.checks_passed,
                    "checks_failed": health.checks_failed,
                    "last_check": health.last_check,
                    "last_error": health.last_error
                }
                for name, health in self.component_health.items()
            }
        }

    def export_health_report(self, export_path: str) -> bool:
        """Export health report"""
        try:
            system_health = self.get_system_health()
            
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "system_health": system_health,
                "component_details": {
                    name: asdict(health)
                    for name, health in self.component_health.items()
                },
                "recent_checks": {
                    key: [asdict(r) for r in self.results[key][-10:]]
                    for key in self.checks
                }
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting health report: {e}")
            return False

    def _update_component_health(self, component: str, result: HealthCheckResult):
        """Update component health based on check result"""
        if component not in self.component_health:
            self.component_health[component] = ComponentHealth(
                component=component,
                status=HealthStatus.UNKNOWN.value,
                last_check=datetime.now().isoformat()
            )
        
        health = self.component_health[component]
        
        # Update check counters
        if result.status == HealthStatus.HEALTHY.value:
            health.checks_passed += 1
        else:
            health.checks_failed += 1
            health.last_error = result.message
        
        # Determine overall component status
        total = health.checks_passed + health.checks_failed
        if total > 0:
            pass_rate = health.checks_passed / total
            
            if pass_rate >= 0.95:
                health.status = HealthStatus.HEALTHY.value
            elif pass_rate >= 0.75:
                health.status = HealthStatus.DEGRADED.value
            else:
                health.status = HealthStatus.UNHEALTHY.value
        
        health.uptime_percent = (health.checks_passed / total * 100) if total > 0 else 0
        health.last_check = datetime.now().isoformat()

    def _load_health_data(self):
        """Load health data from storage"""
        health_file = self.storage_path / "health_status.json"
        if health_file.exists():
            try:
                with open(health_file, 'r') as f:
                    data = json.load(f)
                    for comp_name, comp_data in data.items():
                        self.component_health[comp_name] = ComponentHealth(**comp_data)
            except Exception as e:
                print(f"Error loading health data: {e}")


# Built-in health checks
def create_kafka_check(brokers: List[str]) -> Callable:
    """Create Kafka connectivity check"""
    def check():
        try:
            # Attempt to get metadata
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=brokers,
                request_timeout_ms=5000
            )
            producer.close()
            return (HealthStatus.HEALTHY.value, "Kafka brokers reachable", {})
        except Exception as e:
            return (HealthStatus.UNHEALTHY.value, f"Kafka check failed: {str(e)}", {})
    
    return check


def create_storage_check(path: str) -> Callable:
    """Create storage accessibility check"""
    def check():
        try:
            import os
            if os.path.exists(path):
                disk_usage = os.statvfs(path)
                free_gb = (disk_usage.f_bavail * disk_usage.f_frsize) / (1024**3)
                
                if free_gb < 10:
                    return (HealthStatus.DEGRADED.value,
                           f"Low disk space: {free_gb:.1f}GB free",
                           {"free_gb": free_gb})
                
                return (HealthStatus.HEALTHY.value,
                       f"Storage healthy with {free_gb:.1f}GB free",
                       {"free_gb": free_gb})
            else:
                return (HealthStatus.UNHEALTHY.value,
                       f"Storage path not found: {path}", {})
        except Exception as e:
            return (HealthStatus.UNHEALTHY.value, f"Storage check failed: {str(e)}", {})
    
    return check


def create_database_check(connection_string: str) -> Callable:
    """Create database connectivity check"""
    def check():
        try:
            import sqlite3
            if "sqlite" in connection_string.lower():
                conn = sqlite3.connect(connection_string.replace("sqlite:///", ""))
                conn.close()
                return (HealthStatus.HEALTHY.value, "Database connection successful", {})
            else:
                # For other databases, would need appropriate driver
                return (HealthStatus.UNKNOWN.value, "Database type not supported", {})
        except Exception as e:
            return (HealthStatus.UNHEALTHY.value, f"Database check failed: {str(e)}", {})
    
    return check


# Global health check manager instance
_health_manager = None

def get_health_check_manager(storage_path: str = "/tmp/monitoring/health") -> HealthCheckManager:
    """Get or create global health check manager"""
    global _health_manager
    if _health_manager is None:
        _health_manager = HealthCheckManager(storage_path)
    return _health_manager
