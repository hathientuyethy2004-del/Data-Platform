"""
Example: Load a Parquet file into DuckDB and run a simple aggregation.
Requires: duckdb installed (see requirements.txt)
"""
from analytics_layer import get_analytics_manager
from analytics_layer import get_query_service
import os


def run_example(parquet_path: str):
    # Get query service with duckdb engine
    q = get_query_service(db_path=":memory:", engine="duckdb")
    # Register parquet as table (DuckDB optimized)
    ok = q.register_table_from_parquet("events", parquet_path)
    if not ok:
        print("Failed to register parquet; ensure duckdb is available and file exists")
        return

    res = q.execute("SELECT COUNT(*) as cnt, AVG(value) as avg_value FROM events")
    print("Columns:", res.columns)
    print("Rows:", res.rows)


if __name__ == '__main__':
    sample = os.getenv('SAMPLE_PARQUET', 'data/sample.parquet')
    run_example(sample)
