"""
Correlation Engine
Find correlations between metrics and root causes for issues
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import threading


class CorrelationType(Enum):
    """Types of correlations"""
    METRIC_TO_METRIC = "metric_to_metric"
    ERROR_TO_LATENCY = "error_to_latency"
    RESOURCE_TO_THROUGHPUT = "resource_to_throughput"
    COMPONENT_CASCADE = "component_cascade"
    ANOMALY_TRIGGER = "anomaly_trigger"


@dataclass
class Correlation:
    """Correlation between two events or metrics"""
    correlation_id: str
    timestamp: str
    type: str  # CorrelationType
    
    source_component: str
    source_metric: str
    source_value: float
    
    target_component: str
    target_metric: str
    target_value: float
    
    correlation_strength: float  # 0-1, 1 = perfect correlation
    time_offset_seconds: float  # Delay between source and target
    
    causality_confidence: float = 0.0  # 0-1, likelihood of causality


@dataclass
class RootCause:
    """Root cause analysis result"""
    root_cause_id: str
    timestamp: str
    component: str
    
    primary_issue: str  # The main problem
    contributing_factors: List[str]  # Secondary issues
    affected_components: List[str]  # Components impacted
    
    confidence: float  # 0-1, confidence in root cause
    remediation_steps: List[str]  # Suggested fixes
    
    severity: str  # low, medium, high, critical


class CorrelationEngine:
    """Correlation and root cause analysis engine"""

    def __init__(self, correlation_threshold: float = 0.6):
        """Initialize correlation engine"""
        self.storage_path = Path("monitoring_data/correlations")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.correlation_threshold = correlation_threshold
        
        # Event timeline: {component: [(timestamp, metric, value, type)]}
        self.event_timeline: Dict[str, List[Tuple]] = {}
        
        # Detected correlations
        self.correlations: List[Correlation] = []
        
        # Root causes
        self.root_causes: List[RootCause] = []
        
        # Component dependency graph
        self.component_dependencies: Dict[str, Set[str]] = {}
        
        self.lock = threading.Lock()
        self._load_data()

    def record_event(self, component: str, metric: str, value: float,
                    event_type: str = "metric") -> str:
        """Record an event for correlation analysis"""
        timestamp = datetime.now().isoformat()
        
        with self.lock:
            if component not in self.event_timeline:
                self.event_timeline[component] = []
            
            self.event_timeline[component].append((timestamp, metric, value, event_type))
            
            # Keep only recent events
            cutoff = datetime.now() - timedelta(days=7)
            self.event_timeline[component] = [
                e for e in self.event_timeline[component]
                if datetime.fromisoformat(e[0]) >= cutoff
            ]
            
            # Analyze correlations
            self._analyze_correlations()
            self._save_data()
        
        return f"{component}_{metric}_{timestamp}"

    def register_dependency(self, source_component: str, target_component: str):
        """Register component dependency"""
        with self.lock:
            if source_component not in self.component_dependencies:
                self.component_dependencies[source_component] = set()
            self.component_dependencies[source_component].add(target_component)
            self._save_data()

    def _analyze_correlations(self):
        """Analyze correlations between metrics"""
        components = list(self.event_timeline.keys())
        
        if len(components) < 2:
            return
        
        # Check correlations between all component pairs
        for i, comp1 in enumerate(components):
            for comp2 in components[i+1:]:
                corr = self._calculate_correlation(comp1, comp2)
                if corr and corr.correlation_strength > self.correlation_threshold:
                    # Check if similar correlation already exists
                    exists = any(
                        c.source_component == corr.source_component and
                        c.target_component == corr.target_component and
                        c.source_metric == corr.source_metric and
                        c.target_metric == corr.target_metric
                        for c in self.correlations
                    )
                    
                    if not exists:
                        self.correlations.append(corr)

    def _calculate_correlation(self, comp1: str, comp2: str) -> Optional[Correlation]:
        """Calculate correlation between two components"""
        events1 = self.event_timeline.get(comp1, [])
        events2 = self.event_timeline.get(comp2, [])
        
        if len(events1) < 5 or len(events2) < 5:
            return None
        
        # Find most recent events
        recent1 = events1[-10:]
        recent2 = events2[-10:]
        
        # Calculate simple correlation based on timing and value changes
        time_diffs = []
        value_corrs = []
        
        for e1 in recent1:
            ts1, metric1, val1, _ = e1
            for e2 in recent2:
                ts2, metric2, val2, _ = e2
                
                t1 = datetime.fromisoformat(ts1)
                t2 = datetime.fromisoformat(ts2)
                
                time_diff = abs((t2 - t1).total_seconds())
                
                # Only consider events within 5 minutes
                if time_diff <= 300:
                    time_diffs.append(time_diff)
                    
                    # Simple value correlation
                    if val1 > 0 and val2 > 0:
                        value_corrs.append(val1 * val2)
        
        if not time_diffs:
            return None
        
        # Calculate correlation strength
        avg_time_diff = sum(time_diffs) / len(time_diffs)
        time_correlation = 1.0 - (avg_time_diff / 300)  # 0-1, higher is better
        
        value_correlation = (sum(value_corrs) / len(value_corrs)) if value_corrs else 0.5
        
        # Combined correlation
        correlation_strength = (time_correlation * 0.5 + min(1.0, value_correlation) * 0.5)
        
        # Determine causality confidence based on dependency
        causality = 0.3
        if comp1 in self.component_dependencies and comp2 in self.component_dependencies[comp1]:
            causality = 0.8
        elif comp2 in self.component_dependencies and comp1 in self.component_dependencies[comp2]:
            causality = 0.7
        
        if correlation_strength > self.correlation_threshold:
            return Correlation(
                correlation_id=f"{comp1}_{comp2}_{int(datetime.now().timestamp())}",
                timestamp=datetime.now().isoformat(),
                type=CorrelationType.METRIC_TO_METRIC.value,
                source_component=comp1,
                source_metric=recent1[-1][1],
                source_value=recent1[-1][2],
                target_component=comp2,
                target_metric=recent2[-1][1],
                target_value=recent2[-1][2],
                correlation_strength=min(1.0, correlation_strength),
                time_offset_seconds=avg_time_diff,
                causality_confidence=min(1.0, causality * correlation_strength)
            )
        
        return None

    def analyze_root_cause(self, component: str, issue: str, affected_components: List[str] = None) -> RootCause:
        """Analyze root cause for an issue"""
        root_cause_id = f"{component}_{issue}_{int(datetime.now().timestamp())}"
        
        if affected_components is None:
            affected_components = []
        
        # Find contributing factors
        contributing_factors = self._find_contributing_factors(component)
        
        # Find upstream components that might be root cause
        upstream = self._find_upstream_components(component)
        
        # Calculate confidence
        confidence = 0.5
        if contributing_factors:
            confidence = min(0.95, 0.5 + len(contributing_factors) * 0.1)
        
        # Generate remediation steps
        remediation = self._generate_remediation(issue, upstream, contributing_factors)
        
        # Determine severity
        severity = "medium"
        if len(affected_components) > 3:
            severity = "critical"
        elif len(affected_components) > 1:
            severity = "high"
        elif contributing_factors:
            severity = "medium"
        else:
            severity = "low"
        
        root_cause = RootCause(
            root_cause_id=root_cause_id,
            timestamp=datetime.now().isoformat(),
            component=component,
            primary_issue=issue,
            contributing_factors=contributing_factors,
            affected_components=affected_components,
            confidence=confidence,
            remediation_steps=remediation,
            severity=severity
        )
        
        with self.lock:
            self.root_causes.append(root_cause)
            self._save_data()
        
        return root_cause

    def _find_contributing_factors(self, component: str) -> List[str]:
        """Find contributing factors to issue"""
        factors = []
        
        # Find related correlations
        for corr in self.correlations:
            if corr.target_component == component and corr.correlation_strength > 0.7:
                factors.append(f"{corr.source_component}:{corr.source_metric}")
        
        return factors

    def _find_upstream_components(self, component: str) -> List[str]:
        """Find upstream components in dependency chain"""
        upstream = []
        visited = set()
        
        def traverse(comp, depth=0):
            if depth > 3 or comp in visited:
                return
            visited.add(comp)
            
            for src, targets in self.component_dependencies.items():
                if comp in targets:
                    upstream.append(src)
                    traverse(src, depth + 1)
        
        traverse(component)
        return upstream

    def _generate_remediation(self, issue: str, upstream: List[str], factors: List[str]) -> List[str]:
        """Generate remediation steps"""
        steps = []
        
        # Basic remediation based on issue type
        if "latency" in issue.lower():
            steps.append("Analyze CPU and memory usage on affected component")
            steps.append("Check network connectivity and bandwidth")
            steps.append("Review query execution plans")
        elif "error" in issue.lower():
            steps.append("Check error logs for detailed messages")
            steps.append("Verify data format and schema")
            steps.append("Check upstream data sources")
        elif "throughput" in issue.lower():
            steps.append("Analyze resource utilization")
            steps.append("Check for bottlenecks in pipeline")
            steps.append("Review parallelization settings")
        
        # Add upstream-specific remediation
        if upstream:
            steps.insert(0, f"Check status of upstream components: {', '.join(upstream)}")
        
        return steps

    def get_related_issues(self, component: str, metric: str, days: int = 7) -> List[Dict]:
        """Get issues related to a component"""
        cutoff = datetime.now() - timedelta(days=days)
        
        related = []
        for corr in self.correlations:
            corr_time = datetime.fromisoformat(corr.timestamp)
            if corr_time < cutoff:
                continue
            
            if (corr.source_component == component and corr.source_metric == metric) or \
               (corr.target_component == component and corr.target_metric == metric):
                related.append({
                    "source": f"{corr.source_component}:{corr.source_metric}",
                    "target": f"{corr.target_component}:{corr.target_metric}",
                    "correlation": corr.correlation_strength,
                    "causality": corr.causality_confidence,
                    "time_offset": corr.time_offset_seconds
                })
        
        return related

    def get_correlation_graph(self, days: int = 7) -> Dict:
        """Get correlation graph for visualization"""
        cutoff = datetime.now() - timedelta(days=days)
        
        nodes = set()
        edges = []
        
        for corr in self.correlations:
            corr_time = datetime.fromisoformat(corr.timestamp)
            if corr_time < cutoff:
                continue
            
            if corr.correlation_strength > self.correlation_threshold:
                nodes.add(corr.source_component)
                nodes.add(corr.target_component)
                
                edges.append({
                    "from": corr.source_component,
                    "to": corr.target_component,
                    "weight": corr.correlation_strength,
                    "causality": corr.causality_confidence
                })
        
        return {
            "nodes": list(nodes),
            "edges": edges,
            "timestamp": datetime.now().isoformat()
        }

    def get_root_causes(self, days: int = 7) -> List[RootCause]:
        """Get recent root causes"""
        cutoff = datetime.now() - timedelta(days=days)
        
        result = []
        for cause in self.root_causes:
            cause_time = datetime.fromisoformat(cause.timestamp)
            if cause_time >= cutoff:
                result.append(cause)
        
        return result

    def export_correlation_report(self, output_path: str, days: int = 7) -> bool:
        """Export correlation analysis report"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            recent_corrs = [c for c in self.correlations if datetime.fromisoformat(c.timestamp) >= cutoff]
            recent_causes = [c for c in self.root_causes if datetime.fromisoformat(c.timestamp) >= cutoff]
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "period_days": days,
                "correlation_graph": self.get_correlation_graph(days),
                "correlations": [asdict(c) for c in recent_corrs[:50]],
                "root_causes": [asdict(c) for c in recent_causes],
                "summary": {
                    "total_correlations": len(recent_corrs),
                    "total_root_causes": len(recent_causes),
                    "high_confidence_causes": len([c for c in recent_causes if c.confidence > 0.8])
                }
            }
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting correlation report: {e}")
            return False

    def _load_data(self):
        """Load correlation data from file"""
        data_file = self.storage_path / "correlation_data.json"
        if not data_file.exists():
            return
        
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
                self.correlations = [Correlation(**c) for c in data.get("correlations", [])]
                self.root_causes = [RootCause(**c) for c in data.get("root_causes", [])]
        except Exception as e:
            print(f"Error loading correlation data: {e}")

    def _save_data(self):
        """Save correlation data to file"""
        try:
            data_file = self.storage_path / "correlation_data.json"
            data = {
                "correlations": [asdict(c) for c in self.correlations],
                "root_causes": [asdict(c) for c in self.root_causes]
            }
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving correlation data: {e}")


# Global correlation engine instance
_correlation_engine = None

def get_correlation_engine(correlation_threshold: float = 0.6) -> CorrelationEngine:
    """Get or create global correlation engine"""
    global _correlation_engine
    if _correlation_engine is None:
        _correlation_engine = CorrelationEngine(correlation_threshold)
    return _correlation_engine
