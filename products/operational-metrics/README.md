# Operational Metrics Product

Cross-product operational metrics, SLA monitoring, cost tracking, and infrastructure health monitoring.

## Overview

The Operational Metrics product provides comprehensive visibility into the data platform's operational health and performance.

**Key Features:**
- Real-time SLA compliance tracking
- Cross-product pipeline health monitoring
- Cost analysis and budget tracking
- Infrastructure utilization metrics
- Alert incident management
- Operational dashboards

**Tech Stack:**
- Python 3.9+
- Kafka for metrics ingestion
- Spark 3.2+ for aggregation
- Delta Lake for time-series storage
- FastAPI for REST APIs
- Redis for caching

## Architecture

### Layers

```
Ingestion Layer (src/ingestion/)
├── metrics_collector.py    - Kafka metrics consumption & aggregation
└── Consumes: pipeline logs, alerts, costs, infrastructure metrics

Storage Layer (src/storage/)
├── schemas.py              - Delta Lake schemas (Bronze/Silver/Gold)
└── Bronze → Silver → Gold data pipeline

Processing Layer (src/processing/)
├── kpi_engine.py           - SLA calculations, cost analysis
└── spark_jobs.py           - Spark orchestration (B→S→G)

Serving Layer (src/serving/)
├── api_handlers.py         - REST APIs for dashboards & alerts
└── 8 AWS style endpoints

Monitoring Layer (src/monitoring/)
├── health_checks.py        - Pipeline & infrastructure health
└── 5 health check components

Tests (src/tests/)
└── test_operational_metrics.py - 20+ test cases
```

## Key Components

### 1. Metrics Ingestion

**metrics_collector.py** (400 lines)
- Collects pipeline execution logs from Kafka
- Aggregates data quality metrics from all products
- Tracks API performance metrics
- Monitors infrastructure utilization

**Key Classes:**
- `MetricsCollector`: Ingests and buffers metrics
- `PipelineHealthMetric`: Pipeline execution model
- `DataQualityMetric`: Data quality measurements
- `APIPerformanceMetric`: API response tracking
- `InfrastructureMetric`: Resource utilization

### 2. KPI Calculations

**kpi_engine.py** (400 lines)
- Calculates 5+ SLA metrics
- Performs cost analysis and allocation
- Generates operational dashboards
- Monitors SLA compliance

**Key Classes:**
- `OperationalMetricsCalculator`: Core KPI engine
- `SLAMonitor`: SLA compliance tracking
- `OperationalDashboard`: Dashboard aggregation
- `CostAnalyzer`: Cost breakdown and forecasting

### 3. Storage Schemas

**schemas.py** (350 lines)
- 4 Bronze tables: pipeline_logs, alert_incidents, cost_events, infrastructure_metrics
- 2 Silver tables: pipeline_metrics, sla_metrics
- 4 Gold tables: daily summaries, hourly SLA, cost, alerts

**Data Partitioning:**
- Bronze: by date & product (daily retention: 30 days)
- Silver: by date & product (retention: 90 days)
- Gold: by date & product (retention: 365 days)

### 4. Spark Pipeline

**spark_jobs.py** (350 lines)
- Bronze→Silver: Deduplication, validation of pipeline logs
- Silver→Gold: Hourly & daily aggregations
- Calculates SLA compliance metrics
- Generates cost summaries

**Processing Statistics:**
- ~5B pipeline log records/month
- ~100M alert incidents/month
- Cross-product metric aggregation

### 5. REST APIs

**api_handlers.py** (400 lines)
- 8 REST endpoints for operational dashboards
- SLA compliance reporting
- Cost breakdown endpoints
- Alert management APIs
- Infrastructure utilization views

**Endpoints:**
```
GET  /api/v1/operational/dashboard/overview
GET  /api/v1/operational/sla/compliance
GET  /api/v1/operational/cost/breakdown
POST /api/v1/operational/alerts/create
GET  /api/v1/operational/alerts/incidents
GET  /api/v1/operational/health/pipeline/{product}
GET  /api/v1/operational/metrics/timeseries/{metric}
GET  /api/v1/operational/infrastructure/utilization
GET  /api/v1/operational/summary/operational
```

### 6. Health Monitoring

**health_checks.py** (350 lines)
- 5 parallel health checks (pipeline, freshness, API, infrastructure, SLA)
- Real-time status tracking
- Historical trend analysis
- Automatic incident detection

**Health Check Components:**
1. **Pipeline Health**: Success rates, job durations, record volumes
2. **Data Freshness**: Max age of data across all products
3. **API Availability**: Response times, error rates, uptime
4. **Infrastructure**: CPU, memory, disk utilization
5. **SLA Compliance**: Multi-metric compliance tracking

### 7. Testing

**test_operational_metrics.py** (350 lines)
- 20+ test cases covering:
  - Metrics collection and aggregation
  - SLA calculations and reporting
  - Cost analysis and forecasting
  - Health monitoring workflows
  - Integration scenarios

**Test Coverage:**
- Unit tests for each component
- Integration tests for end-to-end workflows
- Health monitoring scenario tests

## Configuration

**config/product_config.yaml** (272 lines)

Key configurations:
- **Kafka topics**: pipeline_logs, alert_incidents, cost_events, infrastructure_metrics
- **SLA thresholds**: Data freshness, API latency, pipeline success, quality
- **Alert rules**: 4 critical rules with severity levels
- **Cost pricing**: Spark, Kafka, storage cost models
- **Health checks**: Interval and component configuration
- **Spark tuning**: Executors, memory, shuffle parameters

## Running the Product

### Start the Metrics Pipeline

```bash
cd /workspaces/Data-Platform/products/operational-metrics

# Dev environment
python -m src.processing.spark_jobs dev

# Staging
python -m src.processing.spark_jobs staging

# Production
python -m src.processing.spark_jobs prod
```

### Start the API Server

```bash
uvicorn src.serving.api_handlers:app --host 0.0.0.0 --port 8001
```

### Run Health Checks

```bash
python -c "
from src.monitoring.health_checks import OperationalMetricsHealthMonitor
monitor = OperationalMetricsHealthMonitor()
report = monitor.get_health_report()
print(report)
"
```

### Execute Tests

```bash
pytest src/tests/test_operational_metrics.py -v --cov=src
```

## SLA Metrics

| Metric | Target | Warning | Critical | Unit |
|--------|--------|---------|----------|------|
| Data Freshness | 5 min | 10 min | 30 min | minutes |
| API P99 Latency | 800 ms | 1.5 sec | 3 sec | milliseconds |
| Pipeline Success | 99.9% | 99.0% | 95% | percentage |
| Data Quality | 99.5% | 98.0% | 95% | percentage |
| Kafka Lag | 60 sec | 300 sec | 900 sec | seconds |

## Cost Model

**Monthly Cost Breakdown:**
- Spark Compute: ~$3,500 (80 executors × $5/hr × 730 hrs)
- Kafka Streaming: ~$8,760 (5 brokers × $2/hr × 730 hrs)
- Delta Storage: ~$57.50 (2,500 GB × $0.023)
- **Total: ~$12,318/month**

## Alerts

The system monitors 4 critical conditions:

1. **CPU Utilization > 85%** → HIGH severity
2. **Pipeline Failure Rate > 1%** → CRITICAL severity
3. **Data Staleness > 30 min** → HIGH severity
4. **Memory Utilization > 90%** → HIGH severity

Notifications sent via: Slack, Email, PagerDuty

## Data Volumes

**Average Daily:**
- Pipeline logs: ~5M records
- Alert incidents: ~100K records
- Cost events: ~500 records
- Infrastructure metrics: ~1M records

**Storage Usage:**
- Bronze: 500 GB (30-day retention)
- Silver: 750 GB (90-day retention)
- Gold: 1,250 GB (365-day retention)

## API Response Examples

### Dashboard Overview
```json
{
  "timestamp": "2024-02-18T12:00:00Z",
  "products_online": 5,
  "pipelines_running": 12,
  "sla_status": "HEALTHY",
  "cost_this_month": 90360.0,
  "alerts_active": 0,
  "incidents_open": 0
}
```

### SLA Compliance Report
```json
{
  "overall_status": "HEALTHY",
  "sla_checks": [
    {
      "metric": "Data Freshness",
      "target": 5.0,
      "actual": 3.5,
      "status": "HEALTHY"
    }
  ]
}
```

## Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest src/tests/ -v

# Start dev server
uvicorn src.serving.api_handlers:app --reload --port 8001
```

### File Structure

```
operational-metrics/
├── README.md
├── requirements.txt
├── config/
│   ├── product_config.yaml
│   ├── dev.yaml
│   ├── staging.yaml
│   └── prod.yaml
├── src/
│   ├── __init__.py
│   ├── ingestion/
│   │   └── metrics_collector.py       (400L)
│   ├── storage/
│   │   └── schemas.py                 (350L)
│   ├── processing/
│   │   ├── kpi_engine.py              (400L)
│   │   └── spark_jobs.py              (350L)
│   ├── serving/
│   │   └── api_handlers.py            (400L)
│   ├── monitoring/
│   │   └── health_checks.py           (350L)
│   └── tests/
│       └── test_operational_metrics.py (350L)
└── logs/
    └── app.log
```

**Total: 2,900+ lines of Python code**

## Dependencies

Core dependencies in `requirements.txt`:
- pyspark>=3.2.0
- delta-spark>=2.0.0
- fastapi>=0.95.0
- pydantic>=1.10.0
- kafka-python>=2.0.0
- redis>=4.5.0
- pytest>=7.0.0
- pytest-cov>=4.0.0

## Troubleshooting

**Issue: SLA threshold violations**
- Check data freshness delay in Bronze layer
- Verify Spark cluster capacity
- Review Kafka consumer lag

**Issue: Cost overages**
- Analyze job execution times
- Review Spark executor allocation
- Optimize storage cleanup schedules

**Issue: API latency high**
- Check Redis cache hit rate
- Review Spark query plans
- Monitor infrastructure utilization

## Next Steps

1. Implement anomaly detection for metrics
2. Add predictive alerting for SLA violations
3. Auto-scaling recommendations
4. Cost optimization suggestions
5. Integration with cloud cost management services
6. Machine learning models for demand forecasting

## Support

- **Slack**: #data-platform-ops
- **On-Call**: ops@company.com
- **Documentation**: See PRODUCT_README.md in parent directory

---

**Last Updated**: February 18, 2024
**Version**: 1.0.0
**Status**: Production Ready
