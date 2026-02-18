# 🌐 Web User Analytics Product

**Owner**: @team-web  
**SLA**: 99.9% uptime  
**Support**: 24/7 on-call rotation  

---

## 🎯 Overview

Web User Analytics provides comprehensive user behavior insights from web browsers and applications. Tracks user interactions across websites, landing pages, and progressive web apps.

### Key Metrics
- **Unique Visitors** (UV) - Distinct users per day
- **Page Views** (PV) - Total page impressions
- **Bounce Rate** - Users who leave without interacting
- **Session Duration** - Average time per session
- **Conversion Rate** - Goal completion %
- **Traffic Sources** - Referrer attribution
- **Device Breakdown** - Desktop vs Mobile vs Tablet

### Main Use Cases
- User journey tracking and funnel analysis
- Page performance and load time monitoring
- A/B testing and feature adoption metrics
- SEO metrics and search visibility
- Conversion tracking and revenue attribution
- Heatmaps and user behavior analysis

---

## 📊 Data Flow

```
┌──────────────────────────────────────┐
│   Web Browsers (via JavaScript SDK)  │
│   ↓ (web_events topic)               │
├──────────────────────────────────────┤
│   INGESTION LAYER                    │
│   - Kafka Consumer                   │
│   - Event validation                 │
│   - Session tracking                 │
├──────────────────────────────────────┤
│   BRONZE LAYER (Raw)                 │
│   - page_views_bronze                │
│   - click_events_bronze              │
│   - user_sessions_bronze             │
├──────────────────────────────────────┤
│   SILVER LAYER (Cleaned)             │
│   - page_views_silver                │
│   - sessions_silver                  │
│   - user_behavior_silver             │
├──────────────────────────────────────┤
│   GOLD LAYER (Analytics)             │
│   - daily_user_metrics               │
│   - session_analytics                │
│   - page_performance_metrics         │
├──────────────────────────────────────┤
│   SERVING LAYER                      │
│   - REST APIs                        │
│   - Dashboards                       │
│   - Real-time reports                │
└──────────────────────────────────────┘
```

---

## 🏗️ Project Structure

```
products/web-user-analytics/
├── src/
│   ├── ingestion/
│   │   ├── consumer.py              (Kafka consumer for web events)
│   │   ├── schema.py                (Event schema definitions)
│   │   ├── validators.py            (Data validation rules)
│   │   └── session_tracker.py       (Session management)
│   ├── processing/
│   │   ├── spark_jobs.py            (Spark jobs)
│   │   ├── transformations.py       (Session aggregation)
│   │   ├── funnel_analysis.py       (Conversion funnels)
│   │   └── page_analytics.py        (Page-level metrics)
│   ├── storage/
│   │   ├── bronze_schema.py         (Bronze table definitions)
│   │   ├── silver_transforms.py     (Session deduplication)
│   │   ├── gold_metrics.py          (Aggregated analytics)
│   │   └── page_perf_schema.py      (Performance metrics)
│   ├── serving/
│   │   ├── api_handlers.py          (REST API endpoints)
│   │   ├── query_service.py         (Query builder)
│   │   ├── cache_layer.py           (Redis caching)
│   │   └── reporting.py             (Report generation)
│   ├── monitoring/
│   │   ├── health_checks.py         (Service health checks)
│   │   ├── metrics.py               (Product metrics)
│   │   ├── alerts.py                (Alert definitions)
│   │   └── performance_tracking.py  (Performance monitoring)
│   └── tests/
│       ├── test_consumer.py
│       ├── test_session_tracking.py
│       ├── test_analytics.py
│       └── test_api.py
├── config/
│   ├── product_config.yaml
│   ├── environments/
│   │   ├── dev.env
│   │   ├── staging.env
│   │   └── prod.env
├── docs/
│   ├── DESIGN.md                    (Product design & decisions)
│   ├── METRICS.md                   (KPI definitions)
│   ├── API.md                       (REST API documentation)
│   └── TROUBLESHOOTING.md           (Common issues & solutions)
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
- PySpark, Delta Lake, Redis (optional)

### Installation

```bash
cd products/web-user-analytics
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
# Start consumer
make run-local

# Or directly
python -m src.ingestion.consumer
```

---

## 📋 Key Components

### 1. Ingestion (`src/ingestion/`)

Consumes web events from Kafka topic `topic_web_events`.

**Features:**
- Real-time Kafka consumption
- JavaScript event SDK support
- Session tracking & correlation
- Cross-domain tracking
- Bot detection & filtering
- Event enrichment (geographic, device, referrer)

**Event Types:**
- `page_view` - Page loaded
- `click` - User clicked element
- `scroll` - Scroll depth tracking
- `form_submit` - Form submission
- `video_play` - Video interaction
- `custom_event` - App-specific events

### 2. Processing (`src/processing/`)

Transforms raw events into analytics tables.

**Jobs:**
- Event aggregation (minute, hourly, daily windows)
- Session reconstruction (30-min timeout)
- Funnel path analysis
- Page performance aggregation
- Attribution modeling (first-touch, last-touch, multi-touch)

### 3. Storage (`src/storage/`)

Delta Lake with 3-layer lakehouse pattern:

**Bronze**: Raw events ingested as-is
**Silver**: Cleaned, deduplicated, validated with session context
**Gold**: Business-ready analytics tables

### 4. Serving (`src/serving/`)

REST APIs for web analytics queries.

**Key Endpoints:**
```
GET  /api/v1/pages/{page_id}/metrics
GET  /api/v1/funnels/{funnel_id}/conversion
POST /api/v1/sessions/query
GET  /api/v1/users/{user_id}/behavior
POST /api/v1/reports/generate
```

### 5. Monitoring (`src/monitoring/`)

Health checks, metrics, and alerts.

**Metrics:**
- Consumer lag
- Event latency (p50, p95, p99)
- Data quality scores
- Page load performance
- Bot traffic %

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
pytest src/tests/test_session_tracking.py

# Run with coverage
pytest --cov=src src/tests/

# Run performance tests
pytest src/tests/ -m performance
```

---

## 📞 Support & Runbooks

### Common Issues

1. **High consumer lag**
   - Check Kafka broker status
   - Scale up consumer instances
   - Review: [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

2. **Session tracking inaccuracy**
   - Verify session timeout settings (default: 30 min)
   - Check cross-domain tracking configuration
   - Review JavaScript SDK version

3. **Performance degradation**
   - Monitor Spark executor memory
   - Check Delta Lake file compaction
   - Review number of small files in storage

### 24/7 On-Call

- Page @team-web via PagerDuty
- Critical issues: #web-analytics-incidents Slack channel
- Status: https://status.platform.example.com

---

## 📚 Documentation

- [Design Document](docs/DESIGN.md) - Architecture & decisions
- [KPI Definitions](docs/METRICS.md) - Metric specifications
- [API Reference](docs/API.md) - Endpoint documentation
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Common issues

---

## 🔗 Related Products

- **Mobile User Analytics**: `products/mobile-user-analytics/` (complements web)
- **User Segmentation**: `products/user-segmentation/` (consolidates web + mobile)
- **Operational Metrics**: `products/operational-metrics/` (platform KPIs)
