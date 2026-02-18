"""
Quality Monitoring Framework
Data quality checks, SLA enforcement, anomaly detection, and quality scorecards
"""

import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from config.governance_config import governance_config


class QualityCheckType(Enum):
    """Types of quality checks"""
    FRESHNESS = "freshness"         # Data is up-to-date
    COMPLETENESS = "completeness"   # No missing values
    ACCURACY = "accuracy"           # Data is correct
    UNIQUENESS = "uniqueness"       # No duplicates
    VALIDITY = "validity"           # Data format/type correct
    TIMELINESS = "timeliness"       # Data arrives on time
    CONSISTENCY = "consistency"     # Data is consistent across systems


@dataclass
class QualityCheck:
    """A quality check definition"""
    check_id: str
    asset_id: str
    check_type: str
    metric_name: str
    threshold: float  # Pass threshold
    actual_value: float = 0.0
    passed: bool = False
    executed_at: str = ""
    error_message: str = ""


@dataclass
class AnomalyScore:
    """Anomaly detection score"""
    timestamp: str
    asset_id: str
    metric_name: str
    current_value: float
    expected_range: Tuple[float, float]  # min, max
    zscore: float
    is_anomaly: bool
    severity: str  # low, medium, high


@dataclass
class QualityScorecard:
    """Quality scorecard for an asset"""
    asset_id: str
    timestamp: str
    freshness_score: float  # 0-100
    completeness_score: float
    accuracy_score: float
    uniqueness_score: float
    validity_score: float
    overall_score: float  # Weighted average
    status: str  # excellent, good, fair, poor
    checks_passed: int
    checks_failed: int


@dataclass
class SLAViolation:
    """Track SLA violations"""
    violation_id: str
    asset_id: str
    sla_metric: str
    expected_value: float
    actual_value: float
    violated_at: str
    severity: str  # warning, critical


class QualityMonitor:
    """Quality monitoring system"""

    def __init__(self):
        """Initialize quality monitor"""
        self.storage_path = Path(governance_config.quality.quality_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.checks_file = self.storage_path / "quality_checks.json"
        self.scores_file = self.storage_path / "quality_scores.json"
        self.anomalies_file = self.storage_path / "anomalies.json"
        self.sla_violations_file = self.storage_path / "sla_violations.json"
        
        self.checks: Dict[str, QualityCheck] = self._load_checks()
        self.scores: Dict[str, QualityScorecard] = self._load_scores()
        self.anomalies: List[AnomalyScore] = self._load_anomalies()
        self.sla_violations: List[SLAViolation] = self._load_sla_violations()
        
        self.metric_history: Dict[str, List[float]] = {}  # For anomaly detection

    def register_quality_check(self, asset_id: str, check_type: str,
                              metric_name: str, threshold: float) -> str:
        """Register a quality check"""
        from uuid import uuid4
        check_id = str(uuid4())
        
        check = QualityCheck(
            check_id=check_id,
            asset_id=asset_id,
            check_type=check_type,
            metric_name=metric_name,
            threshold=threshold
        )
        
        self.checks[check_id] = check
        self._save_checks()
        
        return check_id

    def execute_quality_check(self, check_id: str, actual_value: float,
                             executed_by: str = "") -> bool:
        """Execute a quality check and record result"""
        if check_id not in self.checks:
            return False
        
        check = self.checks[check_id]
        check.actual_value = actual_value
        check.passed = actual_value >= check.threshold
        check.executed_at = datetime.now().isoformat()
        
        self._save_checks()
        
        # Track for anomaly detection
        if check.asset_id not in self.metric_history:
            self.metric_history[check.asset_id] = []
        
        self.metric_history[check.asset_id].append(actual_value)
        
        return check.passed

    def check_freshness(self, asset_id: str, last_updated: str,
                       expected_hours: int) -> bool:
        """Check data freshness"""
        try:
            last_updated_time = datetime.fromisoformat(last_updated)
            hours_old = (datetime.now() - last_updated_time).total_seconds() / 3600
            is_fresh = hours_old <= expected_hours
            
            # Record check
            freshness_check = None
            for check in self.checks.values():
                if check.asset_id == asset_id and check.check_type == "freshness":
                    freshness_check = check
                    break
            
            if freshness_check:
                self.execute_quality_check(freshness_check.check_id, is_fresh)
            
            return is_fresh
        except Exception as e:
            print(f"Error checking freshness: {e}")
            return False

    def check_completeness(self, asset_id: str, total_records: int,
                          null_records: int) -> float:
        """Check data completeness (% non-null)"""
        if total_records == 0:
            completeness = 0.0
        else:
            completeness = ((total_records - null_records) / total_records) * 100
        
        # Record check
        completeness_check = None
        for check in self.checks.values():
            if check.asset_id == asset_id and check.check_type == "completeness":
                completeness_check = check
                break
        
        if completeness_check:
            self.execute_quality_check(completeness_check.check_id, completeness)
        
        return completeness

    def check_uniqueness(self, asset_id: str, total_records: int,
                        duplicate_records: int) -> float:
        """Check uniqueness (% unique)"""
        if total_records == 0:
            uniqueness = 0.0
        else:
            uniqueness = ((total_records - duplicate_records) / total_records) * 100
        
        return uniqueness

    def check_accuracy(self, asset_id: str, total_records: int,
                      valid_records: int) -> float:
        """Check accuracy (% valid records)"""
        if total_records == 0:
            accuracy = 0.0
        else:
            accuracy = (valid_records / total_records) * 100
        
        # Record check
        accuracy_check = None
        for check in self.checks.values():
            if check.asset_id == asset_id and check.check_type == "accuracy":
                accuracy_check = check
                break
        
        if accuracy_check:
            self.execute_quality_check(accuracy_check.check_id, accuracy)
        
        return accuracy

    def detect_anomalies(self, asset_id: str, metric_name: str,
                        current_value: float, window_size: int = 30) -> AnomalyScore:
        """Detect anomalies using Z-score"""
        from uuid import uuid4
        
        history_key = f"{asset_id}:{metric_name}"
        if history_key not in self.metric_history:
            self.metric_history[history_key] = []
        
        self.metric_history[history_key].append(current_value)
        
        # Keep only recent history
        if len(self.metric_history[history_key]) > window_size:
            self.metric_history[history_key] = self.metric_history[history_key][-window_size:]
        
        # Calculate Z-score
        values = self.metric_history[history_key]
        if len(values) < 2:
            zscore = 0.0
            is_anomaly = False
        else:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 1.0
            zscore = (current_value - mean) / stdev if stdev > 0 else 0.0
            is_anomaly = abs(zscore) > 2.5  # 2.5 standard deviations
        
        # Determine severity
        if is_anomaly:
            if abs(zscore) > 3.5:
                severity = "high"
            elif abs(zscore) > 3.0:
                severity = "medium"
            else:
                severity = "low"
        else:
            severity = "low"
        
        expected_range = (
            min(values) if values else current_value - 10,
            max(values) if values else current_value + 10
        )
        
        anomaly = AnomalyScore(
            timestamp=datetime.now().isoformat(),
            asset_id=asset_id,
            metric_name=metric_name,
            current_value=current_value,
            expected_range=expected_range,
            zscore=zscore,
            is_anomaly=is_anomaly,
            severity=severity
        )
        
        if is_anomaly:
            self.anomalies.append(anomaly)
            self._save_anomalies()
        
        return anomaly

    def calculate_quality_score(self, asset_id: str) -> QualityScorecard:
        """Calculate overall quality score for an asset"""
        from uuid import uuid4
        
        # Get all checks for this asset
        asset_checks = [c for c in self.checks.values() if c.asset_id == asset_id]
        
        # Aggregate by check type
        scores_by_type = {}
        for check_type in QualityCheckType:
            type_checks = [c for c in asset_checks if c.check_type == check_type.value]
            if type_checks:
                passed = sum(1 for c in type_checks if c.passed)
                score = (passed / len(type_checks)) * 100
                scores_by_type[check_type.value] = score
            else:
                scores_by_type[check_type.value] = 0.0
        
        # Weighted scoring (you can adjust weights)
        weights = {
            "freshness": 0.25,
            "completeness": 0.25,
            "accuracy": 0.25,
            "uniqueness": 0.15,
            "validity": 0.10
        }
        
        overall_score = sum(
            scores_by_type.get(check_type, 0) * weight
            for check_type, weight in weights.items()
        )
        
        # Determine status
        if overall_score >= 95:
            status = "excellent"
        elif overall_score >= 85:
            status = "good"
        elif overall_score >= 70:
            status = "fair"
        else:
            status = "poor"
        
        checks_passed = sum(1 for c in asset_checks if c.passed)
        checks_failed = len(asset_checks) - checks_passed
        
        scorecard = QualityScorecard(
            asset_id=asset_id,
            timestamp=datetime.now().isoformat(),
            freshness_score=scores_by_type.get("freshness", 0),
            completeness_score=scores_by_type.get("completeness", 0),
            accuracy_score=scores_by_type.get("accuracy", 0),
            uniqueness_score=scores_by_type.get("uniqueness", 0),
            validity_score=scores_by_type.get("validity", 0),
            overall_score=overall_score,
            status=status,
            checks_passed=checks_passed,
            checks_failed=checks_failed
        )
        
        self.scores[asset_id] = scorecard
        self._save_scores()
        
        return scorecard

    def enforce_sla(self, asset_id: str) -> List[SLAViolation]:
        """Enforce SLA thresholds"""
        from uuid import uuid4
        
        violations = []
        scorecard = self.scores.get(asset_id)
        
        if not scorecard:
            return violations
        
        # Check against SLA thresholds from config
        sla_checks = [
            ("freshness", scorecard.freshness_score, governance_config.quality.sla_freshness_hours),
            ("completeness", scorecard.completeness_score, governance_config.quality.sla_completeness_percent),
            ("accuracy", scorecard.accuracy_score, 98),  # Default 98%
        ]
        
        for sla_metric, actual, expected in sla_checks:
            if actual < expected:
                violation = SLAViolation(
                    violation_id=str(uuid4()),
                    asset_id=asset_id,
                    sla_metric=sla_metric,
                    expected_value=expected,
                    actual_value=actual,
                    violated_at=datetime.now().isoformat(),
                    severity="critical" if actual < (expected * 0.9) else "warning"
                )
                violations.append(violation)
                self.sla_violations.append(violation)
        
        if violations:
            self._save_sla_violations()
        
        return violations

    def get_quality_status(self, asset_id: str) -> Dict:
        """Get quality status for an asset"""
        scorecard = self.scores.get(asset_id)
        violations = [v for v in self.sla_violations if v.asset_id == asset_id]
        
        return {
            "asset_id": asset_id,
            "scorecard": asdict(scorecard) if scorecard else None,
            "sla_violations": [asdict(v) for v in violations],
            "anomalies_count": sum(1 for a in self.anomalies if a.asset_id == asset_id)
        }

    def get_quality_report(self, days: int = 30) -> Dict:
        """Generate quality report"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_violations = [v for v in self.sla_violations
                           if datetime.fromisoformat(v.violated_at) >= cutoff_date]
        recent_anomalies = [a for a in self.anomalies
                          if datetime.fromisoformat(a.timestamp) >= cutoff_date]
        
        # Asset quality ranking
        assets_by_score = sorted(
            [(asset_id, scorecard.overall_score, scorecard.status)
             for asset_id, scorecard in self.scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "period_days": days,
            "total_assets_monitored": len(self.scores),
            "excellent_assets": sum(1 for _, _, status in assets_by_score if status == "excellent"),
            "good_assets": sum(1 for _, _, status in assets_by_score if status == "good"),
            "fair_assets": sum(1 for _, _, status in assets_by_score if status == "fair"),
            "poor_assets": sum(1 for _, _, status in assets_by_score if status == "poor"),
            "total_sla_violations": len(recent_violations),
            "critical_violations": sum(1 for v in recent_violations if v.severity == "critical"),
            "high_severity_anomalies": sum(1 for a in recent_anomalies if a.severity == "high"),
            "worst_performing_assets": assets_by_score[-5:] if len(assets_by_score) >= 5 else assets_by_score,
            "recent_violations": [asdict(v) for v in recent_violations[:10]],
            "recent_anomalies": [asdict(a) for a in recent_anomalies[:10]]
        }

    def export_quality_data(self, export_path: str) -> bool:
        """Export quality monitoring data"""
        try:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "quality_checks": [asdict(c) for c in self.checks.values()],
                "quality_scores": [asdict(s) for s in self.scores.values()],
                "detected_anomalies": [asdict(a) for a in self.anomalies],
                "sla_violations": [asdict(v) for v in self.sla_violations],
                "report": self.get_quality_report()
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting quality data: {e}")
            return False

    def _load_checks(self) -> Dict[str, QualityCheck]:
        """Load quality checks"""
        if not self.checks_file.exists():
            return {}
        
        try:
            with open(self.checks_file, 'r') as f:
                data = json.load(f)
                return {cid: QualityCheck(**cdata) for cid, cdata in data.items()}
        except Exception as e:
            print(f"Error loading quality checks: {e}")
            return {}

    def _load_scores(self) -> Dict[str, QualityScorecard]:
        """Load quality scores"""
        if not self.scores_file.exists():
            return {}
        
        try:
            with open(self.scores_file, 'r') as f:
                data = json.load(f)
                return {asset_id: QualityScorecard(**sdata) for asset_id, sdata in data.items()}
        except Exception as e:
            print(f"Error loading quality scores: {e}")
            return {}

    def _load_anomalies(self) -> List[AnomalyScore]:
        """Load detected anomalies"""
        if not self.anomalies_file.exists():
            return []
        
        try:
            with open(self.anomalies_file, 'r') as f:
                data = json.load(f)
                # Handle tuple in expected_range
                anomalies = []
                for item in data:
                    if isinstance(item.get('expected_range'), list):
                        item['expected_range'] = tuple(item['expected_range'])
                    anomalies.append(AnomalyScore(**item))
                return anomalies
        except Exception as e:
            print(f"Error loading anomalies: {e}")
            return []

    def _load_sla_violations(self) -> List[SLAViolation]:
        """Load SLA violations"""
        if not self.sla_violations_file.exists():
            return []
        
        try:
            with open(self.sla_violations_file, 'r') as f:
                data = json.load(f)
                return [SLAViolation(**vdata) for vdata in data]
        except Exception as e:
            print(f"Error loading SLA violations: {e}")
            return []

    def _save_checks(self):
        """Save quality checks"""
        try:
            data = {cid: asdict(c) for cid, c in self.checks.items()}
            with open(self.checks_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving quality checks: {e}")

    def _save_scores(self):
        """Save quality scores"""
        try:
            data = {asset_id: asdict(s) for asset_id, s in self.scores.items()}
            with open(self.scores_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving quality scores: {e}")

    def _save_anomalies(self):
        """Save anomalies"""
        try:
            # Convert tuples to lists for JSON serialization
            data = []
            for anomaly in self.anomalies:
                adict = asdict(anomaly)
                adict['expected_range'] = list(anomaly.expected_range)
                data.append(adict)
            
            with open(self.anomalies_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving anomalies: {e}")

    def _save_sla_violations(self):
        """Save SLA violations"""
        try:
            data = [asdict(v) for v in self.sla_violations]
            with open(self.sla_violations_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving SLA violations: {e}")


# Global quality monitor instance
_quality_monitor = None

def get_quality_monitor() -> QualityMonitor:
    """Get or create global quality monitor"""
    global _quality_monitor
    if _quality_monitor is None:
        _quality_monitor = QualityMonitor()
    return _quality_monitor
