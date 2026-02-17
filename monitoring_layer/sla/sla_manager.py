"""
SLA Manager
Service Level Agreement tracking and violation detection
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading


class SLAMetric(Enum):
    """SLA metrics"""
    AVAILABILITY = "availability"      # Uptime percentage
    LATENCY = "latency"                # Response time threshold
    THROUGHPUT = "throughput"          # Requests per second
    ERROR_RATE = "error_rate"          # Failed requests percentage
    COMPLETENESS = "completeness"      # Data completeness %


@dataclass
class SLAObjective:
    """Service Level Objective"""
    name: str
    metric: str
    threshold: float
    period_minutes: int  # Measurement period
    target_percentage: float  # e.g., 99.9
    unit: str = ""
    created_at: str = ""


@dataclass
class SLAViolation:
    """SLA violation record"""
    violation_id: str
    objective_name: str
    component: str
    metric: str
    current_value: float
    threshold: float
    violation_time: str
    severity: str  # warning, critical
    resolved: bool = False
    resolution_time: Optional[str] = None


@dataclass
class SLAStatus:
    """Current SLA status"""
    objective_name: str
    component: str
    metric: str
    current_value: float
    target_value: float
    compliance_percent: float  # 0-100
    status: str  # compliant, at_risk, violated
    last_checked: str


class SLAManager:
    """Service Level Agreement management"""

    def __init__(self):
        """Initialize SLA manager"""
        self.storage_path = Path("monitoring_data/sla")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.objectives: Dict[str, SLAObjective] = {}
        self.violations: Dict[str, SLAViolation] = {}
        
        # Metric tracking for SLA evaluation
        self.metric_history: Dict[str, List[tuple]] = {}  # (timestamp, value)
        
        self.lock = threading.Lock()
        self._load_objectives()
        self._load_violations()

    def create_objective(self, name: str, metric: str, threshold: float,
                        period_minutes: int, target_percentage: float,
                        unit: str = "") -> str:
        """Create a new SLA objective"""
        with self.lock:
            if name in self.objectives:
                return ""
            
            objective = SLAObjective(
                name=name,
                metric=metric,
                threshold=threshold,
                period_minutes=period_minutes,
                target_percentage=target_percentage,
                unit=unit,
                created_at=datetime.now().isoformat()
            )
            
            self.objectives[name] = objective
            self._save_objectives()
        
        return name

    def record_metric(self, objective_name: str, value: float) -> bool:
        """Record a metric value for SLA tracking"""
        if objective_name not in self.objectives:
            return False
        
        with self.lock:
            if objective_name not in self.metric_history:
                self.metric_history[objective_name] = []
            
            self.metric_history[objective_name].append(
                (datetime.now().isoformat(), value)
            )
            
            # Keep only recent history
            period_seconds = self.objectives[objective_name].period_minutes * 60
            cutoff_time = time.time() - period_seconds
            
            self.metric_history[objective_name] = [
                (ts, val) for ts, val in self.metric_history[objective_name]
                if time.mktime(datetime.fromisoformat(ts).timetuple()) > cutoff_time
            ]
        
        return True

    def evaluate_objective(self, objective_name: str,
                          component: str) -> SLAStatus:
        """Evaluate SLA objective compliance"""
        if objective_name not in self.objectives:
            return None
        
        objective = self.objectives[objective_name]
        history = self.metric_history.get(objective_name, [])
        
        if not history:
            current_value = 0.0
            compliance = 0.0
        else:
            values = [val for ts, val in history]
            current_value = values[-1]
            
            # Calculate compliance based on metric type
            if objective.metric == "availability":
                compliance = sum(v >= objective.threshold for v in values) / len(values) * 100
            elif objective.metric == "latency":
                compliance = sum(v <= objective.threshold for v in values) / len(values) * 100
            elif objective.metric == "error_rate":
                compliance = sum(v <= objective.threshold for v in values) / len(values) * 100
            else:
                compliance = sum(v >= objective.threshold for v in values) / len(values) * 100
        
        # Determine status
        if compliance >= objective.target_percentage:
            status = "compliant"
        elif compliance >= objective.target_percentage - 10:
            status = "at_risk"
        else:
            status = "violated"
        
        return SLAStatus(
            objective_name=objective_name,
            component=component,
            metric=objective.metric,
            current_value=current_value,
            target_value=objective.threshold,
            compliance_percent=compliance,
            status=status,
            last_checked=datetime.now().isoformat()
        )

    def check_violations(self, objective_name: str, component: str,
                        current_value: float) -> Optional[SLAViolation]:
        """Check for SLA violations"""
        if objective_name not in self.objectives:
            return None
        
        objective = self.objectives[objective_name]
        is_violated = False
        
        # Check violation based on metric type
        if objective.metric in ["latency", "error_rate"]:
            is_violated = current_value > objective.threshold
        else:  # availability, throughput, completeness
            is_violated = current_value < objective.threshold
        
        if not is_violated:
            return None
        
        from uuid import uuid4
        violation = SLAViolation(
            violation_id=str(uuid4()),
            objective_name=objective_name,
            component=component,
            metric=objective.metric,
            current_value=current_value,
            threshold=objective.threshold,
            violation_time=datetime.now().isoformat(),
            severity="critical" if abs(current_value - objective.threshold) > (objective.threshold * 0.2) else "warning"
        )
        
        with self.lock:
            self.violations[violation.violation_id] = violation
            self._save_violations()
        
        return violation

    def resolve_violation(self, violation_id: str) -> bool:
        """Mark violation as resolved"""
        if violation_id not in self.violations:
            return False
        
        with self.lock:
            violation = self.violations[violation_id]
            violation.resolved = True
            violation.resolution_time = datetime.now().isoformat()
            self._save_violations()
        
        return True

    def get_sla_report(self, component: str = None, days: int = 30) -> Dict:
        """Generate SLA compliance report"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "period_days": days,
            "component": component or "all",
            "objectives": {},
            "violations": [],
            "compliance_summary": {}
        }
        
        # Evaluate all objectives
        total_compliance = 0
        compliant_count = 0
        
        for obj_name, objective in self.objectives.items():
            status = self.evaluate_objective(obj_name, component or "all")
            
            if status:
                report["objectives"][obj_name] = asdict(status)
                total_compliance += status.compliance_percent
                if status.status == "compliant":
                    compliant_count += 1
        
        # Get violations in period
        recent_violations = [
            v for v in self.violations.values()
            if datetime.fromisoformat(v.violation_time) >= cutoff_time
        ]
        
        report["violations"] = [asdict(v) for v in recent_violations]
        
        if self.objectives:
            report["compliance_summary"] = {
                "average_compliance": total_compliance / len(self.objectives),
                "compliant_objectives": compliant_count,
                "total_objectives": len(self.objectives),
                "total_violations": len(recent_violations),
                "unresolved_violations": sum(1 for v in recent_violations if not v.resolved)
            }
        
        return report

    def get_objective_history(self, objective_name: str,
                             hours: int = 24) -> Dict:
        """Get history for an SLA objective"""
        if objective_name not in self.objectives:
            return {}
        
        history = self.metric_history.get(objective_name, [])
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_history = [
            (ts, val) for ts, val in history
            if datetime.fromisoformat(ts) >= cutoff_time
        ]
        
        if not recent_history:
            return {"objective": objective_name, "data_available": False}
        
        objective = self.objectives[objective_name]
        values = [val for ts, val in recent_history]
        
        return {
            "objective": objective_name,
            "period_hours": hours,
            "data_available": True,
            "metric": objective.metric,
            "threshold": objective.threshold,
            "target_percentage": objective.target_percentage,
            "samples": {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "current": values[-1] if values else 0
            },
            "timestamps": [ts for ts, _ in recent_history],
            "values": values
        }

    def get_violation_summary(self, days: int = 30) -> Dict:
        """Get violation summary"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        recent_violations = [
            v for v in self.violations.values()
            if datetime.fromisoformat(v.violation_time) >= cutoff_time
        ]
        
        # Group by objective
        by_objective = {}
        for v in recent_violations:
            if v.objective_name not in by_objective:
                by_objective[v.objective_name] = []
            by_objective[v.objective_name].append(v)
        
        # Group by severity
        by_severity = {}
        for v in recent_violations:
            by_severity[v.severity] = by_severity.get(v.severity, 0) + 1
        
        return {
            "period_days": days,
            "total_violations": len(recent_violations),
            "resolved": sum(1 for v in recent_violations if v.resolved),
            "unresolved": sum(1 for v in recent_violations if not v.resolved),
            "by_severity": by_severity,
            "by_objective": {
                obj: len(viols) for obj, viols in by_objective.items()
            }
        }

    def export_sla_report(self, output_path: str, component: str = None) -> bool:
        """Export SLA report"""
        try:
            report = self.get_sla_report(component=component)
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting SLA report: {e}")
            return False

    def _load_objectives(self):
        """Load objectives from file"""
        obj_file = self.storage_path / "objectives.json"
        if not obj_file.exists():
            return
        
        try:
            with open(obj_file, 'r') as f:
                data = json.load(f)
                self.objectives = {
                    name: SLAObjective(**obj_data)
                    for name, obj_data in data.items()
                }
        except Exception as e:
            print(f"Error loading objectives: {e}")

    def _load_violations(self):
        """Load violations from file"""
        viol_file = self.storage_path / "violations.json"
        if not viol_file.exists():
            return
        
        try:
            with open(viol_file, 'r') as f:
                data = json.load(f)
                self.violations = {
                    vid: SLAViolation(**viol_data)
                    for vid, viol_data in data.items()
                }
        except Exception as e:
            print(f"Error loading violations: {e}")

    def _save_objectives(self):
        """Save objectives to file"""
        try:
            obj_file = self.storage_path / "objectives.json"
            with open(obj_file, 'w') as f:
                data = {name: asdict(obj) for name, obj in self.objectives.items()}
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving objectives: {e}")

    def _save_violations(self):
        """Save violations to file"""
        try:
            viol_file = self.storage_path / "violations.json"
            with open(viol_file, 'w') as f:
                data = {vid: asdict(v) for vid, v in self.violations.items()}
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving violations: {e}")


# Global SLA manager instance
_sla_manager = None

def get_sla_manager() -> SLAManager:
    """Get or create global SLA manager"""
    global _sla_manager
    if _sla_manager is None:
        _sla_manager = SLAManager()
    return _sla_manager
