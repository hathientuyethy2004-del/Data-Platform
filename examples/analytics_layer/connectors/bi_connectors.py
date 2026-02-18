"""
BI Connectors
Stubs for exporting data to BI tools, CSV, and serving ODBC/REST endpoints.
"""
import csv
import sqlite3
from pathlib import Path
from typing import Dict, Any, List
from ..query_service import get_query_service

from monitoring_layer.metrics.metrics_collector import get_metrics_collector


class BIConnectors:
    def __init__(self):
        self.export_path = Path("analytics_data/exports")
        self.export_path.mkdir(parents=True, exist_ok=True)
        self.query = get_query_service()
        try:
            self.metrics = get_metrics_collector()
        except Exception:
            self.metrics = None

    def export_to_csv(self, sql: str, output_file: str) -> str:
        res = self.query.execute(sql)
        out = self.export_path / output_file
        with open(out, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(res.columns)
            for r in res.rows:
                writer.writerow(r)
        # Record export metric
        try:
            if self.metrics:
                self.metrics.increment_counter("bi_exports_total", labels={"format": "csv"})
        except Exception:
            pass
        return str(out)

    def get_rest_endpoint(self):
        """Return minimal stub for exposing queries via REST (integrate into dashboard)"""
        return {"status": "ready", "info": "Attach to FastAPI or Flask to serve queries"}

    def export_to_sqlite_db(self, sql: str, db_file: str) -> str:
        """Export query result to a SQLite DB that BI tools can attach to via ODBC"""
        res = self.query.execute(sql)
        out = self.export_path / db_file
        conn = sqlite3.connect(str(out))
        cur = conn.cursor()
        # Create table
        cols = res.columns
        col_defs = ", ".join([f'"{c}" TEXT' for c in cols])
        cur.execute(f"CREATE TABLE IF NOT EXISTS export ({col_defs});")
        # Insert rows
        cur.executemany(f"INSERT INTO export VALUES ({', '.join(['?' for _ in cols])})", res.rows)
        conn.commit()
        conn.close()
        try:
            if self.metrics:
                self.metrics.increment_counter("bi_exports_total", labels={"format": "sqlite"})
        except Exception:
            pass
        return str(out)

    def get_odbc_connection_string(self, sqlite_db_path: str) -> str:
        """Return a simple ODBC connection string for SQLite files (for BI tools)."""
        return f"Driver=SQLite3;Database={sqlite_db_path};" if sqlite_db_path else ""


_bi: BIConnectors = None

def get_bi_connectors() -> BIConnectors:
    global _bi
    if _bi is None:
        _bi = BIConnectors()
    return _bi
