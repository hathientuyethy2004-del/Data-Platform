"""
Anomaly Detector
Statistical anomaly detection and root cause analysis
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import math


class AnomalyType(Enum):
    """Anomaly classification types"""
    SPIKE = "spike"  # Sudden increase
    DIP = "dip"  # Sudden decrease
    TREND = "trend"  # Gradual change
    OUTLIER = "outlier"  # Statistical outlier
    PATTERN_BREAK = "pattern_break"  # Deviation from expected pattern


@dataclass
class AnomalyScore:
    """Anomaly score for a metric value"""
    timestamp: str
    metric_name: str
    component: str
    
    value: float
    mean: float
    std_dev: float
    z_score: float
    percentile: float
    
    anomaly_type: str = ""
    severity: str = "normal"  # low, medium, high, critical
    confidence: float = 0.0  # 0-1
    
    is_anomaly: bool = False


@dataclass
class AnomalyAlert:
    """Alert for detected anomaly"""
    alert_id: str
    timestamp: str
    metric_name: str
    component: str
    value: float
    threshold: float
    anomaly_type: str
    severity: str
    confidence: float
    description: str
    
    acknowledged: bool = False
    acknowledged_at: str = ""


class AnomalyDetector:
    """Statistical anomaly detection"""

    def __init__(self, window_size: int = 100, z_score_threshold: float = 3.0):
        """Initialize anomaly detector"""
        self.storage_path = Path("monitoring_data/anomalies")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.window_size = window_size
        self.z_score_threshold = z_score_threshold
        
        # Metric history: {metric_name: [values]}
        self.metric_history: Dict[str, List[Tuple[str, float]]] = {}
        
        # Baseline statistics
        self.baselines: Dict[str, Dict] = {}
        
        # Detected anomalies
        self.anomalies: List[AnomalyScore] = []
        self.alerts: List[AnomalyAlert] = []
        
        self.lock = threading.Lock()
        self._load_history()

    def record_metric(self, metric_name: str, component: str, value: float) -> Optional[AnomalyScore]:
        """Record metric value and check for anomalies"""
        timestamp = datetime.now().isoformat()
        key = f"{component}:{metric_name}"
        
        with self.lock:
            # Initialize history
            if key not in self.metric_history:
                self.metric_history[key] = []
            
            # Add new value
            self.metric_history[key].append((timestamp, value))
            
            # Keep only recent values
            if len(self.metric_history[key]) > self.window_size:
                self.metric_history[key] = self.metric_history[key][-self.window_size:]
            
            # Calculate baseline if we have enough data
            if len(self.metric_history[key]) < 10:
                return None
            
            # Update baseline
            self._update_baseline(key)
            
            # Detect anomalies
            anomaly = self._detect_anomaly(metric_name, component, value, key)
            
            if anomaly:
                self.anomalies.append(anomaly)
                self._save_history()
            
            return anomaly

    def _detect_anomaly(self, metric_name: str, component: str,
                       value: float, key: str) -> Optional[AnomalyScore]:
        """Detect if value is anomalous"""
        if key not in self.baselines:
            return None
        
        baseline = self.baselines[key]
        mean = baseline["mean"]
        std_dev = baseline["std_dev"]
        
        # Calculate Z-score
        z_score = (value - mean) / std_dev if std_dev > 0 else 0
        
        # Check if anomalous
        is_anomaly = abs(z_score) > self.z_score_threshold
        
        if not is_anomaly:
            return None
        
        # Determine anomaly type
        anomaly_type = self._classify_anomaly(value, mean, baseline)
        
        # Calculate severity and confidence
        severity = self._calculate_severity(abs(z_score))
        confidence = min(1.0, (abs(z_score) - self.z_score_threshold) / 3.0)
        
        # Calculate percentile
        values = [v for _, v in self.metric_history[key]]
        percentile = 100 * sum(1 for v in values if v <= value) / len(values)
        
        return AnomalyScore(
            timestamp=datetime.now().isoformat(),
            metric_name=metric_name,
            component=component,
            value=value,
            mean=mean,
            std_dev=std_dev,
            z_score=z_score,
            percentile=percentile,
            anomaly_type=anomaly_type,
            severity=severity,
            confidence=confidence,
            is_anomaly=True
        )

    def _classify_anomaly(self, value: float, mean: float, baseline: Dict) -> str:
        """Classify type of anomaly"""
        if "recent_mean" in baseline:
            recent_mean = baseline["recent_mean"]
            
            # Check for spike or dip
            if value > mean * 1.5:
                return AnomalyType.SPIKE.value
            elif value < mean * 0.5:
                return AnomalyType.DIP.value
            
            # Check for trend
            if recent_mean > mean * 1.2:
                return AnomalyType.TREND.value
        
        return AnomalyType.OUTLIER.value

    def _calculate_severity(self, z_score: float) -> str:
        """Calculate severity level"""
        if z_score > 10:
            return "critical"
        elif z_score > 6:
            return "high"
        elif z_score > 3:
            return "medium"
        else:
            return "low"

    def _update_baseline(self, key: str):
        """Update baseline statistics"""
        if key not in self.metric_history or len(self.metric_history[key]) < 10:
            return
        
        values = [v for _, v in self.metric_history[key]]
        
        # Calculate mean and std dev
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)
        
        # Calculate recent mean
        recent_values = values[-10:]
        recent_mean = sum(recent_values) / len(recent_values)
        
        self.baselines[key] = {
            "mean": mean,
            "std_dev": std_dev,
            "min": min(values),
            "max": max(values),
            "recent_mean": recent_mean,
            "updated_at": datetime.now().isoformat()
        }

    def create_alert(self, metric_name: str, component: str,
                    value: float, threshold: float,
                    anomaly_type: str, severity: str) -> str:
        """Create anomaly alert"""
        alert_id = f"{component}_{metric_name}_{int(time.time())}"
        
        alert = AnomalyAlert(
            alert_id=alert_id,
            timestamp=datetime.now().isoformat(),
            metric_name=metric_name,
            component=component,
            value=value,
            threshold=threshold,
            anomaly_type=anomaly_type,
            severity=severity,
            confidence=0.95,
            description=f"{severity.upper()} {anomaly_type} in {metric_name}: {value:.2f} (threshold: {threshold:.2f})"
        )
        
        with self.lock:
            self.alerts.append(alert)
            self._save_history()
        
        return alert_id

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge anomaly alert"""
        with self.lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    alert.acknowledged_at = datetime.now().isoformat()
                    self._save_history()
                    return True
        return False

    def get_anomalies(self, component: str = None, metric: str = None,
                     days: int = 1) -> List[AnomalyScore]:
        """Get anomalies for period"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        result = []
        for anomaly in self.anomalies:
            anom_time = datetime.fromisoformat(anomaly.timestamp)
            if anom_time < cutoff_time:
                continue
            
            if component and anomaly.component != component:
                continue
            if metric and anomaly.metric_name != metric:
                continue
            
            result.append(anomaly)
        
        return result

    def get_alerts(self, component: str = None, severity: str = None,
                  acknowledged: bool = False, days: int = 1) -> List[AnomalyAlert]:
        """Get alerts for period"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        result = []
        for alert in self.alerts:
            alert_time = datetime.fromisoformat(alert.timestamp)
            if alert_time < cutoff_time:
                continue
            
            if component and alert.component != component:
                continue
            if severity and alert.severity != severity:
                continue
            if acknowledged and not alert.acknowledged:
                continue
            
            result.append(alert)
        
        return result

    def get_anomaly_summary(self, days: int = 7) -> Dict:
        """Get anomaly summary"""
        anomalies = self.get_anomalies(days=days)
        
        by_component = {}
        by_type = {}
        by_severity = {}
        
        for anomaly in anomalies:
            # By component
            if anomaly.component not in by_component:
                by_component[anomaly.component] = 0
            by_component[anomaly.component] += 1
            
            # By type
            if anomaly.anomaly_type not in by_type:
                by_type[anomaly.anomaly_type] = 0
            by_type[anomaly.anomaly_type] += 1
            
            # By severity
            if anomaly.severity not in by_severity:
                by_severity[anomaly.severity] = 0
            by_severity[anomaly.severity] += 1
        
        return {
            "period_days": days,
            "total_anomalies": len(anomalies),
            "by_component": by_component,
            "by_type": by_type,
            "by_severity": by_severity,
            "avg_confidence": sum(a.confidence for a in anomalies) / len(anomalies) if anomalies else 0
        }

    def get_baseline_metrics(self) -> Dict:
        """Get baseline metrics for all tracked metrics"""
        result = {}
        for key, baseline in self.baselines.items():
            result[key] = baseline.copy()
        return result

    def get_anomalous_metrics(self, hours: int = 24) -> Dict:
        """Get metrics with recent anomalies"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        anomalous = {}
        for anomaly in self.anomalies:
            anom_time = datetime.fromisoformat(anomaly.timestamp)
            if anom_time < cutoff_time:
                continue
            
            key = f"{anomaly.component}:{anomaly.metric_name}"
            if key not in anomalous:
                anomalous[key] = []
            anomalous[key].append({
                "timestamp": anomaly.timestamp,
                "value": anomaly.value,
                "z_score": anomaly.z_score,
                "type": anomaly.anomaly_type,
                "severity": anomaly.severity
            })
        
        return anomalous

    def export_anomalies(self, output_path: str, days: int = 7) -> bool:
        """Export anomalies report"""
        try:
            anomalies = self.get_anomalies(days=days)
            summary = self.get_anomaly_summary(days=days)
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "period_days": days,
                "summary": summary,
                "anomalies": [asdict(a) for a in anomalies[:100]]  # Limit to 100
            }
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting anomalies: {e}")
            return False

    def _load_history(self):
        """Load anomaly history from file"""
        history_file = self.storage_path / "anomaly_history.json"
        if not history_file.exists():
            return
        
        try:
            with open(history_file, 'r') as f:
                data = json.load(f)
                self.anomalies = [AnomalyScore(**record) for record in data.get("anomalies", [])]
                self.alerts = [AnomalyAlert(**record) for record in data.get("alerts", [])]
        except Exception as e:
            print(f"Error loading anomaly history: {e}")

    def _save_history(self):
        """Save anomaly history to file"""
        try:
            history_file = self.storage_path / "anomaly_history.json"
            data = {
                "anomalies": [asdict(a) for a in self.anomalies],
                "alerts": [asdict(a) for a in self.alerts]
            }
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving anomaly history: {e}")


# Global anomaly detector instance
_anomaly_detector = None

def get_anomaly_detector(window_size: int = 100, z_score_threshold: float = 3.0) -> AnomalyDetector:
    """Get or create global anomaly detector"""
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector(window_size, z_score_threshold)
    return _anomaly_detector
