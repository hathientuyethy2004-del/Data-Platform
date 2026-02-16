# Lakehouse Layer - Quick Start Guide

## 🚀 5-Minute Quickstart

### Prerequisites
- ✅ Spark cluster running (from processing layer)
- ✅ Data available in processing layer outputs
- ✅ Python 3.10+, Spark 3.5.0

### Step 1: Install Dependencies

```bash
cd /workspaces/Data-Platform/lakehouse_layer

# Option A: Using pip
pip install pyspark==3.5.0 delta-spark==3.1.0 fastapi==0.104.1 uvicorn==0.24.0

# Option B: Using requirements.txt
pip install -r requirements.txt
```

### Step 2: Run Bronze Ingestion

Ingests raw data from processing layer:

```bash
export PYTHONPATH=/workspaces/Data-Platform/lakehouse_layer:$PYTHONPATH
python jobs/bronze/app_events_ingestion.py
```

**Expected output:**
```
🥉 BRONZE LAYER INGESTION JOB
📖 Reading from: /workspaces/Data-Platform/processing_layer/outputs/events_aggregated_realtime
✅ Transformed 1000 records
📝 Writing to Delta table...
✅ BRONZE INGESTION COMPLETE
```

### Step 3: Run Silver Transformation

Cleans, deduplicates, and enriches data:

```bash
python jobs/silver/transformations.py
```

**Expected output:**
```
🥈 SILVER LAYER TRANSFORMATION JOB
📖 Reading from Bronze: /var/lib/lakehouse/bronze/app_events
✅ Transformed 950 records (50 duplicates removed)
✅ SILVER TRANSFORMATION COMPLETE
```

### Step 4: Run Gold Aggregation

Creates business-ready aggregated tables:

```bash
python jobs/gold/aggregations.py
```

**Expected output:**
```
🏆 GOLD LAYER AGGREGATION JOB
✅ Created 24 hourly metrics
✅ Segmented 500 users
✅ Created daily summaries for 7 days
✅ GOLD AGGREGATION COMPLETE
```

### Step 5: Start API Server

Provides REST API for queries and metadata:

```bash
python api/lakehouse_api.py
```

Access at: `http://localhost:8888`

## 📊 Using the API

### Check Health

```bash
curl http://localhost:8888/health
```

### List All Tables

```bash
curl http://localhost:8888/tables
```

### Query Bronze Layer

```bash
curl http://localhost:8888/tables?layer=bronze
```

### Query Specific Table Metadata

```bash
curl http://localhost:8888/tables/app_events_silver
```

### Preview Table Data

```bash
curl "http://localhost:8888/tables/event_metrics_gold/preview?limit=10"
```

### Execute SQL Query

```bash
curl -X POST http://localhost:8888/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM delta.`/var/lib/lakehouse/gold/event_metrics_gold` LIMIT 10",
    "limit": 1000
  }'
```

### Get Data Lineage

```bash
curl http://localhost:8888/catalog/lineage/event_metrics_gold
```

### Get Catalog Report

```bash
curl http://localhost:8888/catalog
```

## 🐳 Docker Deployment

### Build Image

```bash
cd /workspaces/Data-Platform/lakehouse_layer
docker build -t lakehouse:latest .
```

### Start with Docker Compose

```bash
docker-compose -p lakehouse up -d lakehouse-api
```

### Access API

```bash
curl http://localhost:8888/health
```

### View Logs

```bash
docker-compose -p lakehouse logs -f lakehouse-api
```

### Stop Services

```bash
docker-compose -p lakehouse down
```

## 📊 Monitoring

### Run Health Checks

```bash
python monitoring/health_monitor.py
```

**Generates health report:**
```
🏥 LAKEHOUSE HEALTH REPORT
Status: HEALTHY
Bronze: 3/3 healthy
Silver: 3/3 healthy
Gold: 4/4 healthy
Storage: 2.5 GB across 10 tables
```

## 🔍 Common Operations

### Query All Event Metrics

```bash
curl -X POST http://localhost:8888/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT metric_date, total_events, unique_users FROM delta.`/var/lib/lakehouse/gold/event_metrics_gold` WHERE metric_date = CURRENT_DATE() ORDER BY metric_hour"
  }'
```

### Query User Segments

```bash
curl -X POST http://localhost:8888/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT segment_name, COUNT(*) as user_count FROM delta.`/var/lib/lakehouse/gold/user_segments_gold` WHERE segment_date = CURRENT_DATE() GROUP BY segment_name"
  }'
```

### Get Table Statistics

```bash
curl http://localhost:8888/tables?layer=gold
```

## 🛠️ Configuration

Edit `.env` or set environment variables:

```bash
# Data paths
export LAKEHOUSE_BASE_PATH=/var/lib/lakehouse
export BRONZE_PATH=/var/lib/lakehouse/bronze
export SILVER_PATH=/var/lib/lakehouse/silver
export GOLD_PATH=/var/lib/lakehouse/gold

# Spark
export SPARK_MASTER=spark://spark-master:7077

# Logging
export LOG_LEVEL=INFO
export LOGS_DIR=/var/lib/lakehouse/logs
```

## 🐛 Troubleshooting

### Issue: No data in Bronze layer
**Solution:**
1. Check processing layer has outputs: `ls -la /workspaces/Data-Platform/processing_layer/outputs/`
2. Verify processing jobs have completed
3. Run Bronze ingestion: `python jobs/bronze/app_events_ingestion.py`

### Issue: Spark connection failed
**Solution:**
1. Check Spark is running: `docker ps | grep spark`
2. Verify `SPARK_MASTER` environment variable
3. Check Docker network: `docker network inspect data-platform`

### Issue: "Delta table not found"
**Solution:**
1. Ensure Bronze ingestion has run: `ls -la /var/lib/lakehouse/bronze/`
2. Check table paths exist
3. Run ingestion job again

### Issue: API returns "502 Bad Gateway"
**Solution:**
1. Check logs: `docker logs lakehouse-api`
2. Verify Spark session initialization
3. Restart container: `docker-compose restart lakehouse-api`

## 📈 Next Steps

1. **Explore Data**: Use the REST API to query tables
2. **Add Visualizations**: Connect BI tools (Tableau, Grafana)
3. **Set Up Alerts**: Monitor data quality metrics
4. **Implement MLOps**: Use Gold tables for ML pipelines
5. **Create Views**: Define custom analytical views

## 📚 Documentation

- [Lakehouse README](README.md) - Detailed architecture
- [Delta Lake Docs](https://docs.delta.io/) - Delta Lake reference
- [Spark SQL](https://spark.apache.org/docs/latest/sql-programming-guide.html) - SQL reference

## 🎯 Architecture Overview

```
Data Flow:
Processing Layer Outputs
    ↓
Bronze Layer (Raw) → Silver Layer (Clean) → Gold Layer (Ready)
    ↓           ↓              ↓              ↓
Raw Data    Deduped       Aggregated    Business KPIs
            Enriched      Segmented     Analytics
                                        BI Tools
    
REST API Layer
├── /tables - Table metadata
├── /query - SQL execution
├── /catalog - Data catalog
└── /health - Health checks
```

## 🔗 Integration Points

### With Processing Layer
- Consumes Parquet outputs
- Supports streaming ingestion
- Delta Lake ACID guarantees

### With External Tools
- SQL query support via API
- Metadata export (JSON)
- Data catalog integration
- Lineage tracking

## 📝 Example Workflows

### Daily Analytics Report
```bash
# 1. Wait for processing layer to complete
# 2. Run ingestion: python jobs/bronze/app_events_ingestion.py
# 3. Transform: python jobs/silver/transformations.py
# 4. Aggregate: python jobs/gold/aggregations.py
# 5. Query results via API
# 6. Send to BI tool
```

### Real-time Data Exploration
```bash
# Start API server
# Query using REST endpoints
# Explore with curl or Postman
# Create ad-hoc views for analysis
```

## ✅ Success Criteria

Your lakehouse is working when:
- ✅ Bronze tables contain raw data
- ✅ Silver tables contain cleaned data
- ✅ Gold tables contain aggregated metrics
- ✅ API responds to /health endpoint
- ✅ Catalog tracks all tables and lineage
- ✅ Health monitor reports green status

## 🎓 Learning Resources

1. Start with Bronze layer ingestion
2. Understand Silver transformations
3. Explore Gold aggregations
4. Query via REST API
5. Monitor with health checks
6. Extend with custom jobs

---

**Need Help?** Check logs at `/var/lib/lakehouse/logs/` or review the README.md file.
