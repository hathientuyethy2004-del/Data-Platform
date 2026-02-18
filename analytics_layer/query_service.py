"""
Query Service
Provides a lightweight SQL execution layer and caching for analytical queries.
Uses SQLite for local testing; in real deployments swap to the warehouse (Snowflake/BigQuery/ClickHouse).
"""
import sqlite3
import threading
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# Optional DuckDB support
try:
    import duckdb as _duckdb  # type: ignore
    _DUCKDB_AVAILABLE = True
except Exception:
    _duckdb = None
    _DUCKDB_AVAILABLE = False


@dataclass
class QueryResult:
    timestamp: str
    sql: str
    params: Optional[Tuple]
    rows: List[Tuple]
    columns: List[str]


class QueryService:
    def __init__(self, db_path: Optional[str] = None, engine: str = "sqlite"):
        self.lock = threading.Lock()
        self.db_path = db_path or ":memory:"
        self.engine = engine or "sqlite"

        # Connection handling for different engines
        if self.engine == "duckdb" and _DUCKDB_AVAILABLE:
            # DuckDB uses its own connection object
            self.conn = _duckdb.connect(database=self.db_path)
        else:
            # Fallback to SQLite
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row

        self.cache_path = Path("analytics_data/cache")
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.query_cache: Dict[str, QueryResult] = {}

    def execute(self, sql: str, params: Optional[Tuple] = None, use_cache: bool = False) -> QueryResult:
        key = f"{sql}:{params}"
        if use_cache and key in self.query_cache:
            return self.query_cache[key]

        with self.lock:
            cur = self.conn.cursor()
            if self.engine == "duckdb" and _DUCKDB_AVAILABLE:
                # DuckDB cursor supports execute/fetchall
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                rows = [tuple(r) for r in cur.fetchall()]
                cols = [c[0] for c in cur.description] if cur.description else []
            else:
                cur.execute(sql, params or ())
                rows = [tuple(r) for r in cur.fetchall()]
                cols = [c[0] for c in cur.description] if cur.description else []

        result = QueryResult(timestamp=datetime.now().isoformat(), sql=sql, params=params, rows=rows, columns=cols)

        if use_cache:
            self.query_cache[key] = result
            with open(self.cache_path / (str(abs(hash(key))) + ".json"), "w") as f:
                json.dump(asdict(result), f, default=str)

        return result

    def register_table_from_csv(self, table_name: str, csv_path: str, delimiter: str = ",") -> bool:
        """Load a CSV into the SQLite instance for local analytics/testing"""
        import csv
        # If DuckDB available use its fast CSV reader
        if self.engine == "duckdb" and _DUCKDB_AVAILABLE:
            try:
                # DuckDB can create table directly from CSV
                sql = f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')"
                with self.lock:
                    self.conn.execute(sql)
                return True
            except Exception:
                pass

        # Fallback to SQLite import
        with open(csv_path, "r") as f:
            reader = csv.reader(f, delimiter=delimiter)
            headers = next(reader)
            cols = ",".join([f'"{h}" TEXT' for h in headers])
            create_sql = f"CREATE TABLE IF NOT EXISTS \"{table_name}\" ({cols});"
            with self.lock:
                cur = self.conn.cursor()
                cur.execute(create_sql)
                insert_sql = f"INSERT INTO \"{table_name}\" ({', '.join(['"'+h+'"' for h in headers])}) VALUES ({', '.join(['?' for _ in headers])})"
                cur.executemany(insert_sql, list(reader))
                self.conn.commit()
        return True

    def register_table_from_parquet(self, table_name: str, parquet_path: str) -> bool:
        """Register a Parquet file as a table (DuckDB optimized)"""
        if self.engine == "duckdb" and _DUCKDB_AVAILABLE:
            try:
                sql = f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_parquet('{parquet_path}')"
                with self.lock:
                    self.conn.execute(sql)
                return True
            except Exception:
                return False
        # For SQLite, no native parquet support
        return False

    def explain(self, sql: str) -> str:
        """Return a simple explain plan (SQLite EXPLAIN QUERY PLAN)"""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(f"EXPLAIN QUERY PLAN {sql}")
            rows = cur.fetchall()
        return "\n".join(str(r) for r in rows)


# Singleton
_query_service: Optional[QueryService] = None

def get_query_service(db_path: Optional[str] = None, engine: str = "sqlite") -> QueryService:
    global _query_service
    if _query_service is None:
        _query_service = QueryService(db_path, engine=engine)
    return _query_service
