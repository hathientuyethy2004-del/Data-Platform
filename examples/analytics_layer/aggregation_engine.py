"""
Aggregation Engine
Schedules and runs aggregation jobs (materialized rollups) to support fast analytics.
"""
import threading
import time
import json
from typing import Callable, Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta


class AggregationJob:
    def __init__(self, job_id: str, description: str, fn: Callable, schedule_minutes: int = 60):
        self.job_id = job_id
        self.description = description
        self.fn = fn
        self.schedule_minutes = schedule_minutes
        self.last_run: str = ""
        self.lock = threading.Lock()

    def run(self) -> Dict[str, Any]:
        with self.lock:
            start = datetime.now()
            try:
                result = self.fn()
                status = {"job_id": self.job_id, "status": "success", "started_at": start.isoformat(), "finished_at": datetime.now().isoformat(), "result": str(result)}
            except Exception as e:
                status = {"job_id": self.job_id, "status": "failed", "started_at": start.isoformat(), "finished_at": datetime.now().isoformat(), "error": str(e)}
            self.last_run = datetime.now().isoformat()
            return status


class AggregationEngine:
    def __init__(self):
        self.jobs: Dict[str, AggregationJob] = {}
        self.running = False
        self.thread = None
        self.storage = Path("analytics_data/aggregations")
        self.storage.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

        # Optional integration with monitoring components
        try:
            from monitoring_layer.metrics.metrics_collector import get_metrics_collector
            self.metrics = get_metrics_collector()
        except Exception:
            self.metrics = None

        try:
            from monitoring_layer.alerts.alert_manager import get_alert_manager
            self.alerts = get_alert_manager()
        except Exception:
            self.alerts = None

    def register_job(self, job_id: str, description: str, fn: Callable, schedule_minutes: int = 60):
        with self.lock:
            job = AggregationJob(job_id, description, fn, schedule_minutes)
            self.jobs[job_id] = job
            # Register monitoring metrics for the job if available
            try:
                if self.metrics:
                    self.metrics.register_metric(
                        name=f"aggregation_{job_id}_runs_total",
                        type_="counter",
                        description=f"Total runs for aggregation job {job_id}",
                        labels=["job"]
                    )
                    self.metrics.register_metric(
                        name=f"aggregation_{job_id}_duration_ms",
                        type_="histogram",
                        description=f"Run duration for aggregation job {job_id} in ms",
                        labels=["job"]
                    )
                    self.metrics.register_metric(
                        name=f"aggregation_{job_id}_last_status",
                        type_="gauge",
                        description=f"Last run status for aggregation job {job_id} (1=success,0=fail)",
                        labels=["job"]
                    )
            except Exception:
                pass

            return job

    def run_job_now(self, job_id: str) -> Dict:
        job = self.jobs.get(job_id)
        if not job:
            raise KeyError(f"Job {job_id} not found")
        status = job.run()
        # Record metrics and alerts
        try:
            if self.metrics:
                # Increment run counter
                try:
                    self.metrics.increment_counter(f"aggregation_{job_id}_runs_total", labels={"job": job_id})
                except Exception:
                    pass

                # Compute duration if available
                try:
                    started = datetime.fromisoformat(status.get("started_at"))
                    finished = datetime.fromisoformat(status.get("finished_at"))
                    duration_ms = (finished - started).total_seconds() * 1000
                except Exception:
                    duration_ms = None

                if duration_ms is not None:
                    try:
                        self.metrics.observe_histogram(f"aggregation_{job_id}_duration_ms", duration_ms, labels={"job": job_id})
                    except Exception:
                        pass

                # Set last status gauge
                try:
                    val = 1 if status.get("status") == "success" else 0
                    self.metrics.set_gauge(f"aggregation_{job_id}_last_status", val, labels={"job": job_id})
                except Exception:
                    pass

            # Trigger alert on failure
            if status.get("status") != "success" and self.alerts:
                try:
                    # Use alert manager to evaluate rules for the job failure metric
                    metric_name = f"aggregation_{job_id}_failure"
                    self.alerts.evaluate_and_trigger(metric_name, 1.0, triggered_by=job_id)
                except Exception:
                    pass
        except Exception:
            pass

        self._save_status(job_id, status)
        return status

    def _save_status(self, job_id: str, status: Dict):
        path = self.storage / f"{job_id}_status.json"
        with open(path, "w") as f:
            json.dump(status, f, indent=2, default=str)

    def start_scheduler(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()

    def stop_scheduler(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

    def _scheduler_loop(self):
        while self.running:
            now = datetime.now()
            for job_id, job in list(self.jobs.items()):
                # Determine if job should run
                if not job.last_run:
                    should_run = True
                else:
                    last = datetime.fromisoformat(job.last_run)
                    should_run = (now - last) >= timedelta(minutes=job.schedule_minutes)
                if should_run:
                    status = job.run()
                    self._save_status(job_id, status)
                    # Update a global metric for scheduled runs
                    try:
                        if self.metrics:
                            self.metrics.increment_counter(f"aggregation_{job_id}_scheduled_runs_total", labels={"job": job_id})
                    except Exception:
                        pass
            time.sleep(30)


_engine: AggregationEngine = None

def get_aggregation_engine() -> AggregationEngine:
    global _engine
    if _engine is None:
        _engine = AggregationEngine()
    return _engine
