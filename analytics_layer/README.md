# Analytics Layer

This analytics layer provides lightweight tools to run analytical queries, schedule and store aggregations, define KPIs, build simple materialized cubes, and export data to BI tools.

Quick start:

```python
from analytics_layer import get_analytics_manager
mgr = get_analytics_manager()
q = mgr['query']
q.execute("CREATE TABLE events(ts TEXT, value INT);")
q.execute("INSERT INTO events(ts,value) VALUES ('2026-02-17', 100)")

# Build a cube
cube = mgr['cube']
cube.build_cube('events_agg', 'SELECT COUNT(*) as cnt FROM events')

# Create a KPI
kpi = mgr['kpi']
kpi.create_kpi('events_count', 'Events count', 'SELECT COUNT(*) FROM events', target=1)
print(kpi.evaluate('events_count'))
```

Data storage:

- analytics_data/cache - cached query results
- analytics_data/aggregations - aggregation job statuses
- analytics_data/cubes - materialized cube JSON files
- analytics_data/exports - CSV exports

Integration tests:

Run the smoke tests:

```bash
python analytics_layer/integration_tests.py
```
