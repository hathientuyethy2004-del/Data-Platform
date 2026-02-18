# BI Layer - Business Intelligence & Analytics Platform

Comprehensive Business Intelligence layer providing complete BI capabilities including dimensional modeling, dashboards, reports, metadata management, and data visualization.

## 🎯 Overview

The BI Layer is the analytics and business intelligence engine of the Data Platform, providing:

- **Data Mart Management**: Kimball-style dimensional modeling with fact and dimension tables
- **Dashboard Builder**: Interactive dashboard creation and management
- **Report Generator**: Automated report generation and scheduling
- **Query Optimizer**: SQL query optimization with caching
- **Metadata Management**: Centralized data catalog with lineage tracking
- **Visualization Factory**: Chart and visualization component management
- **REST API**: Complete HTTP API for all BI operations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    REST API Layer                        │
│         (HTTP Endpoints for all BI operations)           │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌──────────┐
   │  Core   │   │ Analysis │   │  Report  │
   │Components   │Engines   │   │ & Export │
   └─────────┘   └──────────┘   └──────────┘
        │
        ├─── Data Mart Engine (Dimensional Modeling)
        ├─── Dashboard Builder (UI Compositions)
        ├─── Report Generator (Templated Reports)
        ├─── Query Optimizer (Performance)
        ├─── Metadata Manager (Data Catalog)
        └─── Chart Factory (Visualizations)
```

## 📦 Components

### 1. Data Mart Engine

Manages dimensional modeling and fact/dimension table schemas.

```python
from bi_layer import get_bi_manager

manager = get_bi_manager()
engine = manager.data_mart

# Create a dimension
dimension = engine.create_dimension(
    name="customer_dimension",
    columns=[
        {"name": "customer_id", "type": "int"},
        {"name": "customer_name", "type": "string"},
        {"name": "segment", "type": "string"}
    ],
    table_name="dim_customer",
    description="Customer dimension",
    scd_type=2  # Type 2 - Slowly Changing Dimension
)

# Create a fact table
fact = engine.create_fact(
    name="sales_fact",
    columns=[
        {"name": "customer_id", "type": "int"},
        {"name": "product_id", "type": "int"},
        {"name": "amount", "type": "decimal"},
        {"name": "quantity", "type": "int"}
    ],
    table_name="fact_sales",
    grain="transaction",  # transaction, daily, hourly
    description="Sales transactions"
)

# Create data mart
mart = engine.create_data_mart(
    mart_name="sales_mart",
    dimensions=["customer_dimension", "product_dimension"],
    facts=["sales_fact"],
    description="Sales analytics mart"
)
```

**Key Features:**
- Dimension and fact table management
- Slowly Changing Dimensions (SCD Type 1, 2, 3)
- Star schema support
- Lineage tracking
- Schema validation

### 2. Dashboard Builder

Create and manage interactive dashboards with widgets.

```python
from bi_layer import get_bi_manager

manager = get_bi_manager()
builder = manager.dashboard

# Create dashboard
dashboard = builder.create_dashboard(
    name="sales_dashboard",
    title="Sales Performance Dashboard",
    description="Real-time sales metrics and trends",
    owner="analytics_team"
)

# Add widgets
from bi_layer.dashboard import Widget

widget = Widget(
    id="revenue_metric",
    type="metric",
    title="Total Revenue",
    query="SELECT SUM(amount) FROM fact_sales",
    position={"x": 0, "y": 0, "width": 3, "height": 2},
    refresh_interval=300
)

builder.add_widget("sales_dashboard", widget)

# Export dashboard
config = builder.export_dashboard("sales_dashboard", format="json")
```

**Widget Types:**
- chart (bar, line, pie, etc.)
- metric (KPI values)
- table (data tables)
- gauge (progress indicators)
- text (descriptions)

### 3. Report Generator

Generate automated reports with scheduling capability.

```python
from bi_layer import get_bi_manager
from bi_layer.reports import ReportFormat, ReportSchedule

manager = get_bi_manager()
generator = manager.reports

# Create report
report = generator.create_report(
    name="monthly_sales",
    title="Monthly Sales Report",
    description="Comprehensive sales analysis",
    owner="sales_team"
)

# Add sections
from bi_layer.reports import ReportSection

section = ReportSection(
    id="revenue_section",
    title="Revenue Analysis",
    content_type="table",
    query="SELECT month, COUNT(*) as transactions, SUM(amount) as revenue FROM sales GROUP BY month",
    order=1
)

generator.add_section("monthly_sales", section)

# Configure scheduling
generator.configure_scheduling(
    report_name="monthly_sales",
    schedule=ReportSchedule.MONTHLY,
    schedule_time="01:00",
    recipients=["team@company.com"]
)

# Generate report
output_path = generator.generate_report(
    "monthly_sales",
    format=ReportFormat.PDF
)
```

**Report Formats:** PDF, Excel, HTML, CSV, JSON

### 4. Query Optimizer

Optimize and cache analytical queries.

```python
from bi_layer import get_bi_manager

manager = get_bi_manager()
optimizer = manager.query_engine

# Parse query
analysis = optimizer.parse_query(
    "SELECT customer_id, SUM(amount) FROM sales GROUP BY customer_id"
)

# Optimize query
plan = optimizer.optimize_query(
    "SELECT * FROM sales WHERE amount > 1000 ORDER BY date"
)

print(f"Estimated cost: {plan.estimated_cost}")
print(f"Suggestions: {plan.index_suggestions}")

# Execute query with caching
result, execution = optimizer.execute_query(
    "SELECT COUNT(*) FROM sales",
    use_cache=True
)

print(f"Execution time: {execution.execution_time_ms}ms")
print(f"Cache hit: {execution.cache_hit}")

# Clear cache when needed
count = optimizer.clear_cache()
```

**Features:**
- Query parsing and analysis
- Execution plan optimization
- Automatic query caching
- Performance metrics tracking
- Cache management

### 5. Metadata Manager

Centralized data catalog with lineage and quality metrics.

```python
from bi_layer import get_bi_manager
from bi_layer.metadata import AssetType, DataClassification

manager = get_bi_manager()
metadata = manager.metadata

# Register asset
asset = metadata.register_asset(
    name="customer_data",
    asset_type=AssetType.DATASET,
    description="Customer master data",
    owner="data_team",
    source_system="CRM"
)

# Add tags
metadata.add_tags(asset.id, ["customer", "production", "critical"])

# Update lineage
metadata.update_lineage(
    asset_id=asset.id,
    upstream=["raw_customers"],
    downstream=["customer_analytics", "customer_reports"]
)

# Update quality metrics
from bi_layer.metadata import DataQualityMetrics

quality = DataQualityMetrics(
    completeness=99.5,
    accuracy=98.0,
    consistency=99.0
)

metadata.update_quality_metrics(asset.id, quality)

# Search assets
results = metadata.search_assets(
    query="customer",
    asset_type=AssetType.TABLE,
    tags=["production"]
)

# Get impact analysis
impact = metadata.get_impact_analysis(asset.id)
print(f"Dependent assets: {impact['all_dependencies']}")
```

**Asset Types:** Dataset, Table, View, Dimension, Fact, Dashboard, Report, Query, Metric

### 6. Chart Factory

Create and manage visualizations.

```python
from bi_layer import get_bi_manager
from bi_layer.visualization import ChartType, ChartTheme

manager = get_bi_manager()
factory = manager.visualization

# Create bar chart
chart = factory.create_bar_chart(
    chart_id="sales_by_region",
    title="Sales by Region",
    category_key="region",
    value_keys=["revenue", "units"]
)

# Create line chart
line_chart = factory.create_line_chart(
    chart_id="revenue_trend",
    title="Revenue Trend",
    time_key="date",
    value_keys=["revenue"]
)

# Create pie chart
pie_chart = factory.create_pie_chart(
    chart_id="market_share",
    title="Market Share",
    label_key="product",
    value_key="sales_amount"
)

# Apply color scheme
factory.apply_color_scheme("sales_by_region", "vibrant")

# Export chart configuration
config = factory.export_chart_config("sales_by_region", format="json")
```

**Chart Types:** Bar, Line, Area, Scatter, Pie, Heatmap, Histogram, Gauge, Sankey, TreeMap, and more

## 🔌 REST API

Complete HTTP API for all BI operations:

```bash
# Data Mart
POST   /api/v1/marts
GET    /api/v1/marts
GET    /api/v1/marts/{mart_name}

# Dimensions & Facts
POST   /api/v1/dimensions
GET    /api/v1/dimensions
POST   /api/v1/facts
GET    /api/v1/facts

# Dashboards
POST   /api/v1/dashboards
GET    /api/v1/dashboards
GET    /api/v1/dashboards/{dashboard_name}
POST   /api/v1/dashboards/{dashboard_name}/widgets

# Reports
POST   /api/v1/reports
GET    /api/v1/reports
POST   /api/v1/reports/{report_name}/generate

# Queries
POST   /api/v1/queries
GET    /api/v1/queries/optimize
POST   /api/v1/queries/cache/clear

# Metadata
POST   /api/v1/metadata/assets
GET    /api/v1/metadata/assets
GET    /api/v1/metadata/assets/{asset_id}

# Charts
POST   /api/v1/charts
GET    /api/v1/charts
GET    /api/v1/charts/{chart_id}

# Health
GET    /api/v1/health
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up data directories
mkdir -p analytics_data/{marts,dashboards,reports,queries,metadata,charts}
```

### Basic Usage

```python
from bi_layer import get_bi_manager

# Initialize BI layer
manager = get_bi_manager()

# Create a simple workflow
print("BI Layer Status:")
print(manager.health_check())
```

### Run Tests

```bash
pytest bi_layer/tests/test_bi_layer.py -v
```

## 📊 Configuration

Configuration is managed in `bi_layer/configs/bi_config.py`:

```python
# Default configuration
{
    'version': '1.0.0',
    'data_mart.storage': 'analytics_data/marts',
    'dashboard.default_theme': 'light',
    'reports.default_format': 'pdf',
    'query.cache_ttl': 3600,
    'metadata.enable_lineage': True,
    'charts.default_width': 800,
    'api.port': 8000
}
```

Override with environment variables:
```bash
export BI_CONFIG_QUERY_CACHE_TTL=7200
export BI_CONFIG_API_PORT=8080
```

## 🔄 Data Flow

```
Raw Data
    ↓
Ingestion Layer
    ↓
Processing Layer (Spark)
    ↓
Lakehouse (Bronze → Silver → Gold)
    ↓
Analytics Layer (Aggregations, KPIs)
    ↓
BI Layer ← You are here
├── Data Mart (Dimensional Model)
├── Dashboards (Real-time visualization)
├── Reports (Scheduled exports)
├── Query Engine (Optimized analytics queries)
├── Metadata Catalog (Data governance)
└── Charts (Reusable visualizations)
    ↓
Serving Layer (APIs, Cache)
    ↓
End Users (Web, Mobile, BI Tools)
```

## 📈 Performance Optimization

- **Query Caching**: Automatic result caching with TTL
- **Index Suggestions**: Index recommendations for slow queries
- **Materialized Views**: Pre-aggregated data marts
- **Partitioned Tables**: Time-based partitioning for facts
- **Connection Pooling**: Efficient database connections

## 🔐 Data Governance

- **Data Classification**: Public, Internal, Confidential, Restricted
- **Lineage Tracking**: Complete data lineage from source to dashboard
- **Quality Metrics**: Completeness, accuracy, consistency tracking
- **Access Control**: Role-based access management (future)
- **Audit Logging**: All operations tracked

## 🤝 Integration Points

- **Ingestion Layer**: Consumes processed lakehouse data
- **Analytics Layer**: Builds upon aggregation and KPI engines
- **Monitoring Layer**: Sends metrics and alerts
- **Governance Layer**: Registers assets in data catalog
- **Serving Layer**: Provides data to end users

## 📚 Best Practices

1. **Dimensional Modeling**
   - Use conformed dimensions across marts
   - Keep dimensions small for performance
   - Implement slowly changing dimensions appropriately

2. **Dashboard Design**
   - Keep dashboards focused on specific use cases
   - Use consistent color schemes
   - Implement real-time refresh only when necessary

3. **Report Generation**
   - Schedule reports during off-peak hours
   - Use templates for consistent formatting
   - Archive old reports for compliance

4. **Query Optimization**
   - Use WHERE clauses to filter early
   - Leverage materialized views
   - Monitor cache hit rates

5. **Metadata Management**
   - Register all data assets
   - Maintain up-to-date lineage
   - Track data quality metrics

## 🧪 Testing

```bash
# Run all tests
pytest bi_layer/tests/ -v

# Run specific test class
pytest bi_layer/tests/test_bi_layer.py::TestDataMartEngine -v

# Run with coverage
pytest bi_layer/tests/ --cov=bi_layer
```

## 📝 Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from bi_layer import get_bi_manager
manager = get_bi_manager()
# Now all operations will be logged
```

## 🔗 Related Documentation

- [Data Platform Architecture](../COMPLETE_ARCHITECTURE.md)
- [Lakehouse Layer](../lakehouse_layer/README.md)
- [Analytics Layer](../analytics_layer/README.md)
- [Monitoring Layer](../monitoring_layer/README.md)

## 👥 Contributing

To extend the BI Layer:

1. Add new component in appropriate module
2. Implement health_check() method
3. Add REST API endpoint
4. Write tests
5. Update documentation

## 📄 License

Part of Data Platform - All rights reserved

## 🆘 Support

For issues and questions:
- Check test cases for usage examples
- Review component README files
- Check main platform documentation

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Status**: Production Ready
