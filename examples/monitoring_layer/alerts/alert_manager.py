"""
Alert Manager
Alert rules, incident tracking, and notification management
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from threading import Lock


class Severity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AlertRule:
    """Alert rule definition"""
    rule_id: str
    name: str
    metric: str
    condition: str  # e.g., "> 80", "< 10", "== 0"
    threshold: float
    severity: str
    enabled: bool = True
    notification_channels: List[str] = None
    cooldown_minutes: int = 5
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = ["default"]


@dataclass
class Alert:
    """Alert instance"""
    alert_id: str
    rule_id: str
    rule_name: str
    metric: str
    value: float
    severity: str
    status: str
    timestamp: str
    message: str
    triggered_by: str = ""
    triggered_count: int = 1
    acknowledged_at: str = ""
    acknowledged_by: str = ""
    resolved_at: str = ""
    resolved_by: str = ""
    details: Dict = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class Incident:
    """Incident grouping alerts"""
    incident_id: str
    alert_ids: List[str] = None
    severity: str = Severity.HIGH.value
    status: str = AlertStatus.TRIGGERED.value
    start_time: str = ""
    end_time: str = ""
    title: str = ""
    description: str = ""
    assigned_to: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.alert_ids is None:
            self.alert_ids = []
        if self.tags is None:
            self.tags = []
        if not self.start_time:
            self.start_time = datetime.now().isoformat()


@dataclass
class NotificationChannel:
    """Notification channel configuration"""
    channel_type: str  # email, slack, webhook, pagerduty
    channel_name: str
    config: Dict
    enabled: bool = True


class AlertManager:
    """Manages alert rules, incidents, and notifications"""

    def __init__(self, storage_path: str = "/tmp/monitoring/alerts"):
        """Initialize alert manager"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        self.incidents: Dict[str, Incident] = {}
        self.channels: Dict[str, NotificationChannel] = {}
        self.last_triggered: Dict[str, datetime] = {}  # For cooldown tracking
        self.lock = Lock()
        
        self._load_alert_data()

    def register_rule(self, rule: AlertRule) -> bool:
        """Register an alert rule"""
        if rule.rule_id in self.rules:
            return False
        
        with self.lock:
            self.rules[rule.rule_id] = rule
        
        return True

    def register_channel(self, channel: NotificationChannel) -> bool:
        """Register notification channel"""
        if channel.channel_name in self.channels:
            return False
        
        with self.lock:
            self.channels[channel.channel_name] = channel
        
        return True

    def evaluate_and_trigger(self, metric: str, value: float,
                            triggered_by: str = "") -> Optional[Alert]:
        """Evaluate rules against metric and trigger if threshold met"""
        alerts = []
        
        for rule_id, rule in self.rules.items():
            if not rule.enabled or rule.metric != metric:
                continue
            
            # Check cooldown
            if rule_id in self.last_triggered:
                if datetime.now() - self.last_triggered[rule_id] < timedelta(minutes=rule.cooldown_minutes):
                    continue
            
            # Evaluate condition
            if self._evaluate_condition(value, rule.condition, rule.threshold):
                alert = self._create_alert(rule, value, triggered_by)
                
                with self.lock:
                    self.alerts[alert.alert_id] = alert
                    self.last_triggered[rule_id] = datetime.now()
                    self._try_group_incident(alert)
                
                alerts.append(alert)
                
                # Send notifications
                self._send_notifications(rule, alert)
        
        return alerts[0] if alerts else None

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        if alert_id not in self.alerts:
            return False
        
        with self.lock:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED.value
            alert.acknowledged_at = datetime.now().isoformat()
            alert.acknowledged_by = acknowledged_by
        
        return True

    def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve an alert"""
        if alert_id not in self.alerts:
            return False
        
        with self.lock:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.RESOLVED.value
            alert.resolved_at = datetime.now().isoformat()
            alert.resolved_by = resolved_by
        
        return True

    def suppress_alert(self, alert_id: str, duration_minutes: int = 60) -> bool:
        """Suppress an alert temporarily"""
        if alert_id not in self.alerts:
            return False
        
        with self.lock:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.SUPPRESSED.value
        
        return True

    def get_active_alerts(self) -> List[Alert]:
        """Get all active (non-resolved) alerts"""
        with self.lock:
            return [
                alert for alert in self.alerts.values()
                if alert.status != AlertStatus.RESOLVED.value
            ]

    def get_alerts_by_severity(self, severity: str) -> List[Alert]:
        """Get alerts by severity"""
        with self.lock:
            return [
                alert for alert in self.alerts.values()
                if alert.severity == severity and alert.status != AlertStatus.RESOLVED.value
            ]

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        with self.lock:
            alerts = sorted(
                self.alerts.values(),
                key=lambda a: a.timestamp,
                reverse=True
            )
            return alerts[:limit]

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get incident details"""
        return self.incidents.get(incident_id)

    def get_open_incidents(self) -> List[Incident]:
        """Get all open incidents"""
        with self.lock:
            return [
                incident for incident in self.incidents.values()
                if incident.status != AlertStatus.RESOLVED.value
            ]

    def close_incident(self, incident_id: str, resolved_by: str) -> bool:
        """Close an incident"""
        if incident_id not in self.incidents:
            return False
        
        with self.lock:
            incident = self.incidents[incident_id]
            incident.status = AlertStatus.RESOLVED.value
            incident.end_time = datetime.now().isoformat()
        
        return True

    def assign_incident(self, incident_id: str, assign_to: str) -> bool:
        """Assign incident to team member"""
        if incident_id not in self.incidents:
            return False
        
        with self.lock:
            self.incidents[incident_id].assigned_to = assign_to
        
        return True

    def get_alert_statistics(self) -> Dict:
        """Get alert statistics"""
        with self.lock:
            alerts = list(self.alerts.values())
            
            total = len(alerts)
            triggered = sum(1 for a in alerts if a.status == AlertStatus.TRIGGERED.value)
            acknowledged = sum(1 for a in alerts if a.status == AlertStatus.ACKNOWLEDGED.value)
            resolved = sum(1 for a in alerts if a.status == AlertStatus.RESOLVED.value)
            
            by_severity = {
                Severity.CRITICAL.value: sum(1 for a in alerts if a.severity == Severity.CRITICAL.value),
                Severity.HIGH.value: sum(1 for a in alerts if a.severity == Severity.HIGH.value),
                Severity.MEDIUM.value: sum(1 for a in alerts if a.severity == Severity.MEDIUM.value),
                Severity.LOW.value: sum(1 for a in alerts if a.severity == Severity.LOW.value),
            }
            
            return {
                "total_alerts": total,
                "triggered": triggered,
                "acknowledged": acknowledged,
                "resolved": resolved,
                "by_severity": by_severity,
                "critical_count": by_severity[Severity.CRITICAL.value],
                "open_incidents": len(self.get_open_incidents())
            }

    def export_incidents(self, export_path: str) -> bool:
        """Export incidents report"""
        try:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "statistics": self.get_alert_statistics(),
                "open_incidents": [
                    asdict(incident)
                    for incident in self.get_open_incidents()
                ],
                "recent_alerts": [
                    asdict(alert)
                    for alert in self.get_alert_history(50)
                ]
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting incidents: {e}")
            return False

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        try:
            if ">" in condition:
                return value > threshold
            elif "<" in condition:
                return value < threshold
            elif "==" in condition:
                return value == threshold
            elif ">=" in condition:
                return value >= threshold
            elif "<=" in condition:
                return value <= threshold
            else:
                return False
        except:
            return False

    def _create_alert(self, rule: AlertRule, value: float, triggered_by: str) -> Alert:
        """Create alert instance"""
        import uuid
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        
        return Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            rule_name=rule.name,
            metric=rule.metric,
            value=value,
            severity=rule.severity,
            status=AlertStatus.TRIGGERED.value,
            timestamp=datetime.now().isoformat(),
            message=f"Alert: {rule.name} - Metric '{rule.metric}' is {value} (condition: {rule.condition} {rule.threshold})",
            triggered_by=triggered_by
        )

    def _try_group_incident(self, alert: Alert):
        """Try to group alert into existing incident"""
        # Find related open incident
        for incident in self.incidents.values():
            if (incident.status != AlertStatus.RESOLVED.value and
                incident.severity == alert.severity):
                # Group into existing incident
                incident.alert_ids.append(alert.alert_id)
                incident.triggered_count = len(incident.alert_ids)
                return
        
        # Create new incident
        import uuid
        incident_id = f"incident_{uuid.uuid4().hex[:8]}"
        new_incident = Incident(
            incident_id=incident_id,
            alert_ids=[alert.alert_id],
            severity=alert.severity,
            title=f"Incident: {alert.rule_name}",
            description=alert.message
        )
        
        self.incidents[incident_id] = new_incident

    def _send_notifications(self, rule: AlertRule, alert: Alert):
        """Send notifications through configured channels"""
        for channel_name in rule.notification_channels:
            if channel_name not in self.channels:
                continue
            
            channel = self.channels[channel_name]
            if not channel.enabled:
                continue
            
            self._notify(channel, alert)

    def _notify(self, channel: NotificationChannel, alert: Alert):
        """Send notification through channel"""
        # In production, would integrate with actual services
        # For now, just log
        notification = {
            "channel": channel.channel_name,
            "alert_id": alert.alert_id,
            "severity": alert.severity,
            "message": alert.message,
            "timestamp": datetime.now().isoformat()
        }
        print(f"[NOTIFICATION] {notification}")

    def _load_alert_data(self):
        """Load alert data from storage"""
        rules_file = self.storage_path / "rules.json"
        incidents_file = self.storage_path / "incidents.json"
        
        if rules_file.exists():
            try:
                with open(rules_file, 'r') as f:
                    rules_data = json.load(f)
                    for rule_dict in rules_data:
                        rule = AlertRule(**rule_dict)
                        self.rules[rule.rule_id] = rule
            except Exception as e:
                print(f"Error loading rules: {e}")
        
        if incidents_file.exists():
            try:
                with open(incidents_file, 'r') as f:
                    incidents_data = json.load(f)
                    for incident_dict in incidents_data:
                        incident = Incident(**incident_dict)
                        self.incidents[incident.incident_id] = incident
            except Exception as e:
                print(f"Error loading incidents: {e}")


# Global alert manager instance
_alert_manager = None

def get_alert_manager(storage_path: str = "/tmp/monitoring/alerts") -> AlertManager:
    """Get or create global alert manager"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(storage_path)
    return _alert_manager
