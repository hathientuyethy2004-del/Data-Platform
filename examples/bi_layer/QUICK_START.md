# BI Layer - Quick Start Guide

## Overview

The BI Layer provides comprehensive Business Intelligence capabilities including dimensional modeling, dashboards, reports, and data visualization.

## Installation

```bash
# Install BI layer dependencies
pip install -r requirements.txt
```

## Basic Usage (5 minutes)

### 1. Initialize BI Manager

```python
from bi_layer import get_bi_manager

# Get the global BI manager instance
manager = get_bi_manager()
```

### 2. Create a Simple Data Mart

```python
# Create a dimension
dim = manager.data_mart.create_dimension(
    name="products",
    columns=[
        {"name": "product_id", "type": "int"},
        {"name": "product_name", "type": "string"}
    ],
    table_name="dim_products"
)

# Create a fact table
fact = manager.data_mart.create_fact(
    name="sales",
    columns=[
        {"name": "product_id", "type": "int"},
        {"name": "amount", "type": "decimal"}
    ],
    table_name="fact_sales",
    grain="transaction"
)

# Create data mart
mart = manager.data_mart.create_data_mart(
    mart_name="sales_mart",
    dimensions=["products"],
    facts=["sales"]
)

print(f"✓ Created mart: {mart['name']}")
```

### 3. Create a Dashboard

```python
from bi_layer.dashboard import Widget

# Create dashboard
dashboard = manager.dashboard.create_dashboard(
    name="my_dashboard",
    title="My Dashboard"
)

# Add metric widget
widget = Widget(
    id="metric_1",
    type="metric",
    title="Total Sales",
    query="SELECT SUM(amount) FROM fact_sales"
)

manager.dashboard.add_widget("my_dashboard", widget)
print("✓ Dashboard created with metrics")
```

### 4. Generate a Report

```python
from bi_layer.reports import ReportFormat

# Create report
report = manager.reports.create_report(
    name="daily_report",
    title="Daily Sales Report"
)

# Generate
output = manager.reports.generate_report(
    "daily_report",
    format=ReportFormat.HTML
)

print(f"✓ Report generated: {output}")
```

### 5. Query Data

```python
# Execute query with caching
result, execution = manager.query_engine.execute_query(
    "SELECT COUNT(*) FROM fact_sales"
)

print(f"Execution time: {execution.execution_time_ms}ms")
```

### 6. Manage Metadata

```python
from bi_layer.metadata import AssetType

# Register asset
asset = manager.metadata.register_asset(
    name="sales_data",
    asset_type=AssetType.DATASET,
    owner="analytics"
)

# Add tags
manager.metadata.add_tags(asset.id, ["important", "sales"])

# Search
results = manager.metadata.search_assets(
    query="sales",
    tags=["important"]
)

print(f"✓ Found {len(results)} assets")
```

### 7. Create Charts

```python
# Create bar chart
chart = manager.visualization.create_bar_chart(
    chart_id="sales_chart",
    title="Sales by Region",
    category_key="region",
    value_keys=["amount"]
)

# Apply color scheme
manager.visualization.apply_color_scheme("sales_chart", "vibrant")

print("✓ Chart created with colors")
```

### 8. Check System Health

```python
health = manager.health_check()

print("\nSystem Status:")
for component, status in health.items():
    print(f"  {component}: {status['status']}")
```

## Advanced Features

### Dimensional Modeling with SCD

```python
# Slowly Changing Dimension Type 2 (track history)
customer_dim = manager.data_mart.create_dimension(
    name="customers",
    columns=[...],
    table_name="dim_customers",
    scd_type=2  # 1=Replace, 2=History, 3=Alternative
)
```

### Scheduled Reports

```python
from bi_layer.reports import ReportSchedule

manager.reports.configure_scheduling(
    report_name="daily_report",
    schedule=ReportSchedule.DAILY,
    schedule_time="06:00",
    recipients=["team@company.com"]
)
```

### Data Lineage

```python
# Track data flow
manager.metadata.update_lineage(
    asset_id="dataset_id",
    upstream=["source_1", "source_2"],
    downstream=["dashboard_1", "report_1"]
)

# Get impact analysis
impact = manager.metadata.get_impact_analysis("dataset_id")
print(f"This dataset affects {impact['dependency_count']} assets")
```

### Query Optimization

```python
# Analyze query
plan = manager.query_engine.optimize_query(
    "SELECT ... FROM ..."
)

print(f"Estimated cost: {plan.estimated_cost}")
print(f"Suggestions: {plan.index_suggestions}")

# Clear cache if needed
manager.query_engine.clear_cache()
```

## Running Examples

```bash
# Run comprehensive examples
python bi_layer/examples/bi_examples.py
```

## Running Tests

```bash
# Run all tests
pytest bi_layer/tests/ -v

# Run with coverage
pytest bi_layer/tests/ --cov=bi_layer --cov-report=html
```

## Configuration

Edit `bi_layer/configs/bi_config.py` or use environment variables:

```bash
# Set configuration via environment
export BI_CONFIG_QUERY_CACHE_TTL=7200
export BI_CONFIG_API_PORT=8080
```

## REST API (Future)

The BI layer provides a complete REST API:

```bash
# Start API server (example)
python -m bi_layer.api

# Then make requests
curl http://localhost:8000/api/v1/health
```

## Common Use Cases

### Sales Analytics Dashboard
See `example_dashboard()` in `bi_layer/examples/bi_examples.py`

### Monthly Report Generation
See `example_reports()` in `bi_layer/examples/bi_examples.py`

### Data Quality Monitoring
See `example_metadata()` in `bi_layer/examples/bi_examples.py`

### Query Performance
See `example_queries()` in `bi_layer/examples/bi_examples.py`

## Troubleshooting

### Issue: "Module not found"
```bash
pip install -r bi_layer/requirements.txt
```

### Issue: "Permission denied" creating files
```bash
mkdir -p analytics_data/{marts,dashboards,reports,queries,metadata,charts}
chmod 755 analytics_data/*
```

### Issue: Slow queries
```python
# Use query optimizer
plan = manager.query_engine.optimize_query(query)
print(plan.index_suggestions)
```

## Next Steps

1. Read the full [README.md](README.md)
2. Explore [examples/bi_examples.py](examples/bi_examples.py)
3. Check [tests/test_bi_layer.py](tests/test_bi_layer.py) for more examples
4. Configure for your environment in [configs/bi_config.py](configs/bi_config.py)

## Support

- Documentation: See README.md
- Examples: See examples/bi_examples.py
- Tests: See tests/test_bi_layer.py
- Issues: Check the main platform issues

---

**Current Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: February 2026
