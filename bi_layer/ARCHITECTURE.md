# BI Layer - Component Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      BI LAYER                               │
│           Business Intelligence & Analytics Engine          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
    ┌────────┐           ┌────────┐           ┌────────┐
    │ Data   │           │ Serving│           │ Serving│
    │ Layer  │           │ APIs   │           │ Cache  │
    └────────┘           └────────┘           └────────┘
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                         │
              Core BI Components
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │  Data    │    │Dashboard │    │  Report  │
   │  Mart    │    │ Builder  │    │Generator │
   └──────────┘    └──────────┘    └──────────┘
        │                │                │
        ▼                ▼                ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │ Query    │    │Metadata  │    │  Chart   │
   │Optimizer │    │ Manager  │    │ Factory  │
   └──────────┘    └──────────┘    └──────────┘
```

## Component Details

### 1. Data Mart Engine (`data_mart/`)

**Purpose**: Manages dimensional modeling and fact/dimension tables

**Key Classes**:
- `Dimension`: Represents a dimension table with natural keys
- `Fact`: Represents a fact table with measures
- `DataMartEngine`: Central manager for data mart operations

**Key Methods**:
- `create_dimension()`: Create a dimension table
- `create_fact()`: Create a fact table
- `create_data_mart()`: Combine dimensions and facts into a mart
- `get_mart_schema()`: Get complete schema for a mart

**Storage**: `analytics_data/marts/metadata.json`

**Example**:
```python
engine = manager.data_mart
dim = engine.create_dimension("customer", [...], "dim_customer")
fact = engine.create_fact("sales", [...], "fact_sales", "transaction")
mart = engine.create_data_mart("sales_mart", ["customer"], ["sales"])
```

### 2. Dashboard Builder (`dashboard/`)

**Purpose**: Create and manage interactive dashboards with widgets

**Key Classes**:
- `Widget`: Individual dashboard widget (chart, metric, table, etc.)
- `Dashboard`: Container for widgets with layout
- `DashboardBuilder`: Manager for dashboard operations

**Key Methods**:
- `create_dashboard()`: Create new dashboard
- `add_widget()`: Add widget to dashboard
- `update_widget()`: Modify widget configuration
- `export_dashboard()`: Export as JSON/YAML
- `import_dashboard()`: Import from configuration

**Widget Types**: chart, metric, table, gauge, text

**Storage**: `analytics_data/dashboards/dashboards.json`

**Example**:
```python
builder = manager.dashboard
dash = builder.create_dashboard("sales_dash", "Sales Dashboard")
widget = Widget(id="metric_1", type="metric", title="Revenue", query="...")
builder.add_widget("sales_dash", widget)
```

### 3. Report Generator (`reports/`)

**Purpose**: Generate automated reports with scheduling

**Key Classes**:
- `ReportSection`: Section within a report
- `Report`: Collection of sections with metadata
- `ReportGenerator`: Manager for report operations
- `ReportExecution`: Record of report generation

**Key Methods**:
- `create_report()`: Create new report
- `add_section()`: Add section to report
- `configure_scheduling()`: Set up report schedule
- `generate_report()`: Generate report in specified format

**Report Formats**: PDF, Excel, HTML, CSV, JSON

**Scheduling**: Once, Daily, Weekly, Monthly

**Storage**: `analytics_data/reports/reports.json`

**Example**:
```python
gen = manager.reports
report = gen.create_report("monthly", "Monthly Report")
section = ReportSection(id="sec1", title="Sales", content_type="table", query="...")
gen.add_section("monthly", section)
gen.configure_scheduling("monthly", ReportSchedule.MONTHLY, "01:00", ["email@company.com"])
```

### 4. Query Optimizer (`query_engine/`)

**Purpose**: Optimize queries and manage execution caching

**Key Classes**:
- `QueryPlan`: Execution plan with optimization suggestions
- `QueryExecution`: Record of query execution
- `QueryOptimizer`: Query optimization and caching engine

**Key Methods**:
- `parse_query()`: Analyze query structure
- `optimize_query()`: Generate optimization plan
- `execute_query()`: Execute with automatic caching
- `clear_cache()`: Clear query cache
- `get_query_statistics()`: Get performance metrics

**Features**:
- Automatic result caching with TTL
- Index recommendations
- Cost estimation
- Performance tracking

**Storage**: `analytics_data/queries/query_cache.json`

**Example**:
```python
opt = manager.query_engine
plan = opt.optimize_query("SELECT ... FROM ... WHERE ...")
result, exec = opt.execute_query(query, use_cache=True)
print(f"Time: {exec.execution_time_ms}ms, Cached: {exec.cache_hit}")
```

### 5. Metadata Manager (`metadata/`)

**Purpose**: Centralized data catalog with lineage and quality tracking

**Key Classes**:
- `DataAsset`: Represents a data asset in the catalog
- `AssetType`: Enumeration of asset types
- `DataClassification`: Data privacy levels
- `DataQualityMetrics`: Quality measurements
- `MetadataManager`: Manager for metadata operations

**Key Methods**:
- `register_asset()`: Register new asset
- `add_tags()`: Add tags to asset
- `update_lineage()`: Track data flow
- `update_quality_metrics()`: Update DQ scores
- `search_assets()`: Search by various criteria
- `get_impact_analysis()`: Find dependent assets

**Asset Types**: Dataset, Table, View, Dimension, Fact, Dashboard, Report, Query, Metric

**Classifications**: Public, Internal, Confidential, Restricted

**Storage**: `analytics_data/metadata/catalog.json`

**Example**:
```python
meta = manager.metadata
asset = meta.register_asset("sales_data", AssetType.DATASET, owner="team")
meta.add_tags(asset.id, ["important", "production"])
meta.update_lineage(asset.id, upstream=["raw"], downstream=["dash"])
impact = meta.get_impact_analysis(asset.id)
```

### 6. Chart Factory (`visualization/`)

**Purpose**: Create and manage visualization components

**Key Classes**:
- `ChartAxis`: Configuration for chart axes
- `ChartSeries`: Data series in chart
- `ChartConfig`: Complete chart configuration
- `ChartFactory`: Manager for chart operations

**Key Methods**:
- `create_chart()`: Create generic chart
- `create_bar_chart()`: Create bar chart
- `create_line_chart()`: Create line chart
- `create_pie_chart()`: Create pie chart
- `add_series()`: Add data series
- `apply_color_scheme()`: Apply predefined colors
- `export_chart_config()`: Export configuration

**Chart Types**: Bar, Line, Area, Scatter, Pie, Heatmap, Histogram, Gauge, Sankey, TreeMap, Bubble, Waterfall, Sunburst

**Color Schemes**: default, pastel, dark, vibrant, custom

**Storage**: `analytics_data/charts/charts.json`

**Example**:
```python
viz = manager.visualization
chart = viz.create_bar_chart("sales_chart", "Sales", "region", ["amount"])
viz.apply_color_scheme("sales_chart", "vibrant")
config = viz.export_chart_config("sales_chart", format="json")
```

### 7. REST API (`api/`)

**Purpose**: HTTP endpoints for all BI operations

**Key Classes**:
- `BIRestAPI`: Main API handler

**Endpoints**:
- `/api/v1/marts`: Data mart operations
- `/api/v1/dimensions`: Dimension management
- `/api/v1/facts`: Fact table management
- `/api/v1/dashboards`: Dashboard operations
- `/api/v1/reports`: Report operations
- `/api/v1/queries`: Query execution
- `/api/v1/metadata/assets`: Asset management
- `/api/v1/charts`: Chart operations
- `/api/v1/health`: Health check

### 8. Orchestrator (`orchestrator.py`)

**Purpose**: Coordinate multi-step BI workflows

**Key Classes**:
- `BIOrchestrator`: Workflow execution engine

**Key Methods**:
- `execute_workflow()`: Execute workflow steps
- `create_sales_analytics_workspace()`: Pre-built workflow

**Features**:
- Multi-step workflows
- Execution history tracking
- Workflow reporting
- Step-by-step status tracking

## Data Flow

```
User Request
    │
    ▼
API Layer / Manager
    │
    ├─→ Data Mart ────────┐
    ├─→ Dashboard Builder │
    ├─→ Report Generator  ├─→ Storage (JSON)
    ├─→ Query Optimizer   │
    ├─→ Metadata Manager  │
    └─→ Chart Factory ────┘
    │
    ▼
Response/Output
```

## Configuration Hierarchy

```
Defaults (bi_config.py)
    ↓
Environment Variables (BI_CONFIG_*)
    ↓
Configuration File (config.json)
    ↓
Runtime Overrides
```

## Storage Structure

```
analytics_data/
├── marts/
│   └── schema.json        # Data mart definitions
├── dashboards/
│   └── dashboards.json    # Dashboard configurations
├── reports/
│   ├── reports.json       # Report definitions
│   ├── {report_name}/     # Report outputs
│   │   └── report_YYYYMMDD_HHMMSS.{format}
├── queries/
│   └── query_cache.json   # Cached query results
├── metadata/
│   └── catalog.json       # Asset catalog & lineage
└── charts/
    └── charts.json        # Chart configurations
```

## Integration Points

```
BI Layer
    ├─ Consumes: Lakehouse data (Bronze/Silver/Gold)
    ├─ Consumes: Analytics Layer aggregations/KPIs
    ├─ Provides: Dashboards and Reports
    ├─ Registers: Assets with Governance Layer
    ├─ Sends: Metrics to Monitoring Layer
    ├─ Serves: Data to Serving Layer
    └─ Uses: Config from Platform Config
```

## Performance Characteristics

| Component | Operation | Typical Time |
|-----------|-----------|--------------|
| Data Mart | Create dimension | <1ms |
| Data Mart | Create fact | <1ms |
| Dashboard | Add widget | <1ms |
| Dashboard | Export config | <10ms |
| Report | Generate HTML | <100ms |
| Report | Generate PDF | 100-500ms |
| Query | Parse query | ~1ms |
| Query | Optimize query | ~5ms |
| Query | Execute (cached) | <1ms |
| Query | Execute (uncached) | Variable |
| Metadata | Register asset | <1ms |
| Metadata | Search assets | 1-10ms |
| Chart | Create chart | <1ms |
| Chart | Apply scheme | <1ms |

## Scalability Considerations

- **Data Marts**: Support hundreds of dimensions/facts per mart
- **Dashboards**: Support 100+ widgets per dashboard
- **Reports**: Support unlimited sections
- **Query Cache**: LRU cache with configurable TTL
- **Metadata**: Catalog supports 1000+ assets
- **Charts**: Performance-optimized for interactive visualization

## Security & Governance

- Data Classification levels (Public → Restricted)
- Asset tagging and classification
- Lineage tracking for compliance
- Data quality metrics monitoring
- Owner assignment and tracking
- Future: Role-based access control

---

**Architecture Version**: 1.0.0  
**Last Updated**: February 2026  
**Status**: Production Ready
