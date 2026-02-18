"""
KPI Engine
Define and evaluate business KPIs using the QueryService and AggregationEngine.
"""
from dataclasses import dataclass, asdict
from typing import Callable, Dict, Any, Optional, List
from datetime import datetime
from .query_service import get_query_service
from typing import cast
import threading


@dataclass
class KPI:
    name: str
    description: str
    sql: str
    params: tuple = ()
    target: Optional[float] = None
    higher_is_better: bool = True


class KPIEngine:
    def __init__(self):
        self.kpis: Dict[str, KPI] = {}
        self.query = get_query_service()
        # Optional integration points
        try:
            from analytics_layer.aggregation_engine import get_aggregation_engine
            self.aggregation = get_aggregation_engine()
        except Exception:
            self.aggregation = None

        try:
            from monitoring_layer.alerts.alert_manager import get_alert_manager
            self.alerts = get_alert_manager()
        except Exception:
            self.alerts = None

        self.lock = threading.Lock()

    def create_kpi(self, name: str, description: str, sql: str, params: tuple = (), target: Optional[float] = None, higher_is_better: bool = True) -> KPI:
        kpi = KPI(name=name, description=description, sql=sql, params=params, target=target, higher_is_better=higher_is_better)
        self.kpis[name] = kpi
        return kpi

    def evaluate(self, name: str) -> Dict[str, Any]:
        if name not in self.kpis:
            raise KeyError("KPI not found")
        kpi = self.kpis[name]
        res = self.query.execute(kpi.sql, kpi.params, use_cache=False)
        # Expect single numeric value in first column of first row
        value = None
        if res.rows and len(res.rows[0]) > 0:
            try:
                value = float(res.rows[0][0])
            except Exception:
                value = None
        status = "unknown"
        if value is not None and kpi.target is not None:
            if kpi.higher_is_better:
                status = "met" if value >= kpi.target else "not_met"
            else:
                status = "met" if value <= kpi.target else "not_met"
        return {"kpi": asdict(kpi), "value": value, "status": status, "evaluated_at": datetime.now().isoformat()}

    def schedule_kpi_evaluation(self, name: str, schedule_minutes: int = 60):
        """Register KPI evaluation as an aggregation job so it runs periodically."""
        if self.aggregation is None:
            raise RuntimeError("Aggregation engine not available")

        def _eval_job():
            try:
                result = self.evaluate(name)
                # If KPI not met, trigger alert
                if result.get("status") == "not_met" and self.alerts:
                    try:
                        metric_name = f"kpi_{name}_violation"
                        self.alerts.evaluate_and_trigger(metric_name, 1.0, triggered_by=name)
                    except Exception:
                        pass
                return result
            except Exception as e:
                return {"error": str(e)}

        job_id = f"kpi_{name}_job"
        with self.lock:
            self.aggregation.register_job(job_id, f"Evaluate KPI {name}", _eval_job, schedule_minutes=schedule_minutes)
        return job_id


_engine: KPIEngine = None

def get_kpi_engine() -> KPIEngine:
    global _engine
    if _engine is None:
        _engine = KPIEngine()
    return _engine
