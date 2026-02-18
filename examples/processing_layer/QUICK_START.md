# 🚀 Processing Layer - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
cd /workspaces/Data-Platform/processing_layer
pip install -r requirements.txt
```

### 2. Start Spark Cluster (Docker)

```bash
# From processing_layer directory
docker-compose -p data-platform up -d

# Verify all services started
docker-compose -p data-platform ps
```

**Expected output:**
```
NAME                      STATUS
spark-master              Up
spark-worker-1            Up
spark-worker-2            Up
processing-orchestrator    Up
```

### 3. Run Streaming Jobs

```bash
# Terminal 1: Event Aggregation
python jobs/streaming/event_aggregation.py

# Terminal 2: Clickstream Analysis (in another terminal)
python jobs/streaming/clickstream_analysis.py

# Terminal 3: CDC Transformation (in another terminal)
python jobs/streaming/cdc_transformation.py
```

**Expected logs:**
```
🚀 Starting Event Aggregation Job
📥 Setting up Kafka stream reader for topics: ['topic_app_events']
✅ Kafka stream reader created
📝 Parsing Kafka messages
📊 Aggregating by user and event type (1-minute windows)
✅ Event Aggregation Job started
```

### 4. Monitor Spark

Open browser and visit:
- **Spark Master UI**: http://localhost:8080
- **Worker 1**: http://localhost:8081
- **Worker 2**: http://localhost:8082

### 5. Run a Batch Job

```bash
# Hourly aggregation
python jobs/batch/hourly_aggregate.py

# Daily summary
python jobs/batch/daily_summary.py

# User segmentation
python jobs/batch/user_segmentation.py --lookback-days 30
```

### 6. Check Output Files

```bash
ls -la outputs/
# Should show:
# - events_aggregated_realtime/
# - clickstream_sessions/
# - cdc_transformed/
# - hourly_aggregates/
# - daily_summaries/
# - user_segments/
```

---

## Common Commands

### View Streaming Job Logs

```bash
# Real-time logs
tail -f logs/event_aggregation.log

# JSON-formatted logs (for tools like jq)
tail -f logs/event_aggregation.log | jq .

# Search for errors
grep ERROR logs/*.log
```

### Stop Everything

```bash
# Stop Spark cluster
docker-compose -p data-platform down

# Or stop individual job (from terminal running it)
Ctrl+C
```

### Run Orchestrator (All Jobs)

```bash
python orchestrator.py
```

This starts all enabled jobs (streaming + batch) simultaneously.

---

## Verify Setup

### Check Spark Master is Running

```bash
curl http://localhost:8080/api/v1/applications
# Should return JSON with Spark applications
```

### Check Kafka Connection

```bash
# List Kafka topics
/workspaces/Data-Platform/ingestion_layer/utils/kafka_utils.py \
  --bootstrap-server localhost:29092 \
  --list

# Consume from a topic
kafka-console-consumer --bootstrap-server localhost:29092 --topic topic_app_events --max-messages 1
```

### Test Job Execution

```bash
# Quick test - runs once and exits
python -c "
from utils.spark_utils import create_spark_session
spark = create_spark_session('test')
print('✅ Spark session created')
spark.stop()
"
```

---

## Troubleshooting

### Job Hangs on Startup

**Problem:** Job seems to hang after "Starting job..."

**Solution:** 
- Ensure Kafka is running and accessible
- Check logs: `tail -f logs/orchestrator.log`
- Verify `KAFKA_BOOTSTRAP_SERVER` environment variable is set

### Out of Memory

**Problem:** `java.lang.OutOfMemoryError: Java heap space`

**Solution:**
```bash
# Increase memory
export EXECUTOR_MEMORY=4g
export DRIVER_MEMORY=4g

# Restart job
python jobs/streaming/event_aggregation.py
```

### No Data in Output

**Problem:** Job runs but produces no output files

**Solution:**
1. Check if Kafka topics have data: Verify ingestion layer is running
2. Check if streaming batches are getting data:
   ```bash
   # Look for successfully processed batches in logs
   grep "successfully" logs/event_aggregation.log
   ```
3. Ensure output directory is writable:
   ```bash
   ls -la outputs/
   chmod 777 outputs/
   ```

### Port Already in Use

**Problem:** `Address already in use` error

**Solution:**
```bash
# Kill process using port 8080
lsof -i :8080
kill -9 <PID>

# Or use different port
# Edit docker-compose.yml and change port mappings
```

---

## Next Steps

1. **Review** the main [README.md](README.md) for detailed architecture
2. **Explore** example queries in [EXAMPLES.md](EXAMPLES.md) (if exists)
3. **Configure** job schedules in `configs/spark_config.py`
4. **Add** custom streaming/batch jobs following the patterns
5. **Monitor** outputs in `outputs/` directory

---

## Architecture Quick Reference

```
Data Flow:
Kafka Topics (ingestion_layer)
    ↓
Spark Streaming Jobs (process in real-time)
    ├─ Event Aggregation (1-min windows)
    ├─ Clickstream Analysis (session tracking)
    ├─ Data Enrichment (join with lookups)
    └─ CDC Transformation (upsert handling)
    ↓
Parquet Files (outputs/)
    ↓
Spark Batch Jobs (scheduled analytics)
    ├─ Hourly Aggregate (metrics rollup)
    ├─ Daily Summary (KPI calculation)
    └─ User Segmentation (behavior analysis)
    ↓
Parquet Output Files → Ready for BI/Analytics
```

---

**Happy Processing! 🚀**

For detailed documentation, see [README.md](README.md)
