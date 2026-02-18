# 📱 Mobile User Analytics Product

**Owner**: @team-mobile  
**SLA**: 99.9% uptime  
**Support**: 24/7 on-call rotation

---

## 🎯 Overview

Mobile User Analytics provides comprehensive user behavior insights from mobile applications.

### Key Metrics
- **DAU** (Daily Active Users)
- **Session Length** (average, median)
- **Event Volume** (events/minute)
- **Retention** (day 1, day 7, day 30)
- **Crash Rate** per version

### Main Use Cases
- User journey tracking
- Session analysis
- Feature adoption metrics
- Performance monitoring
- Crash reporting

---

## 📊 Data Flow

```
┌─────────────────────────────────────┐
│   Mobile Apps (iOS/Android)         │
│   ↓ (mobile_app_events topic)       │
├─────────────────────────────────────┤
│   INGESTION LAYER                   │
│   - Kafka Consumer                  │
│   - Schema validation               │
│   - Event enrichment                │
├─────────────────────────────────────┤
│   BRONZE LAYER (Raw)                │
│   - app_events_bronze               │
│   - Partitioned by: event_date      │
├─────────────────────────────────────┤
│   SILVER LAYER (Cleaned)            │
│   - app_events_silver               │
│   - Deduplication                   │
│   - Quality validation              │
├─────────────────────────────────────┤
│   GOLD LAYER (Analytics)            │
│   - daily_user_metrics              │
│   - session_analytics               │
├─────────────────────────────────────┤
│   SERVING LAYER                     │
│   - REST APIs                       │
│   - Dashboards                      │
│   - Analytics tools                 │
└─────────────────────────────────────┘
```

---

## 🏗️ Project Structure

```
products/mobile-user-analytics/
├── src/
│   ├── ingestion/
│   │   ├── consumer.py              (Kafka consumer logic)
│   │   ├── schema.py                (Event schema definition)
│   │   └── validators.py            (Data validation rules)
│   ├── processing/
│   │   ├── spark_jobs.py            (Spark jobs)
│   │   ├── transformations.py       (Data transformations)
│   │   └── aggregations.py          (Metric aggregations)
│   ├── storage/
│   │   ├── bronze_schema.py         (Bronze table definitions)
│   │   ├── silver_transforms.py     (Silver layer logic)
│   │   └── gold_metrics.py          (Gold analytics tables)
│   ├── serving/
│   │   ├── api_handlers.py          (REST API endpoints)
│   │   ├── query_service.py         (Query building)
│   │   └── cache_layer.py           (Caching logic)
│   ├── monitoring/
│   │   ├── health_checks.py         (Health checks)
│   │   ├── metrics.py               (Product metrics)
│   │   └── alerts.py                (Alert definitions)
│   └── tests/
│       ├── test_consumer.py
│       ├── test_processing.py
│       └── test_api.py
├── config/
│   ├── product_config.yaml
│   ├── environments/
│   │   ├── dev.env
│   │   ├── staging.env
│   │   └── prod.env
├── docs/
│   ├── DESIGN.md                    (Product design)
│   ├── METRICS.md                   (KPI definitions)
│   ├── API.md                       (API documentation)
│   └── TROUBLESHOOTING.md           (Common issues)
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── requirements.txt
├── Dockerfile
├── Makefile
└── pytest.ini
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Spark 3.2+
- Kafka 7.5+
- PySpark, Delta Lake

### Installation

```bash
cd products/mobile-user-analytics
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp config/environments/dev.env .env

# Edit configuration
vim .env
```

### Running Locally

```bash
# Start using Makefile
make run-local

# Or directly with Python
python -m src.ingestion.consumer
```

---

## 📋 Key Components

### 1. Ingestion (`src/ingestion/`)

Reads mobile app events from Kafka topic `topic_app_events`.

**Features:**
- Real-time Kafka consumption
- Schema validation (Avro)
- Event enrichment (user context, app metadata)
- Error handling & retry logic

**Configuration:**
```yaml
ingestion:
  topics: [topic_app_events]
  consumer_group: mobile-analytics-consumer
  batch_size: 1000
  timeout_ms: 30000
```

### 2. Processing (`src/processing/`)

Transforms raw events into analytics tables.

**Jobs:**
- Event aggregation (1-min, hourly, daily windows)
- Session tracking
- User funnel analysis

### 3. Storage (`src/storage/`)

Delta Lake with 3-layer lakehouse pattern:

**Bronze**: Raw events ingested as-is
**Silver**: Cleaned, deduplicated, validated data
**Gold**: Business-ready analytics tables

### 4. Serving (`src/serving/`)

REST APIs for analytics queries.

**Endpoints:**
```
GET  /api/v1/users/{user_id}/summary
GET  /api/v1/metrics/daily
POST /api/v1/query
```

### 5. Monitoring (`src/monitoring/`)

Health checks, metrics, and alerts.

**Metrics:**
- Consumer lag
- Processing latency
- Data quality scores

---

## 🔄 Deployment

### Local Development

```bash
make dev-up          # Start services
make dev-down        # Stop services
```

### Staging

```bash
make deploy-staging
```

### Production

```bash
make deploy-prod
```

---

## 📊 Testing

```bash
# Run all tests
make test

# Run specific test file
pytest src/tests/test_consumer.py

# Run with coverage
pytest --cov=src src/tests/
```

---

## 📞 Support & Runbooks

### Common Issues

1. **High consumer lag**
   - Check Kafka broker status
   - Scale up consumer instances
   - See: [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

2. **Data quality issues**
   - Run quality checks: `python src/monitoring/quality_checks.py`
   - Check schema evolution
   - Review recent deployments

### 24/7 On-Call

- Page @team-mobile via PagerDuty
- Critical issues: #mobile-analytics-incidents Slack channel
- Status page: https://status.platform.example.com

---

## 📚 Documentation

- [Design Document](docs/DESIGN.md)
- [KPI Definitions](docs/METRICS.md)
- [API Reference](docs/API.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

---

## 🔗 Related Products

- **Web User Analytics**: `products/web-user-analytics/`
- **User Segmentation**: `products/user-segmentation/` (consolidates mobile + web)
- **Operational Metrics**: `products/operational-metrics/`

