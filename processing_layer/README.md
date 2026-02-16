# 🎯 Processing Layer - Apache Spark Data Processing

> Real-time and batch data processing using Apache Spark and Kafka streaming

## 📋 Overview

The **Processing Layer** transforms raw ingested data from Kafka into valuable business insights through:

- **Real-time Streaming**: Process events as they arrive with low latency
- **Batch Analytics**: Run comprehensive analytical jobs on historical data
- **Data Enrichment**: Enhance raw events with contextual information
- **Aggregations**: Calculate metrics and KPIs automatically
- **User Profiling**: Segment and analyze user behavior patterns

```
INGESTION LAYER (Kafka Streams)
    ↓ (validate, normalize)
KAFKA TOPICS (4 main topics)
    ↓ (consume events)
PROCESSING LAYER (Spark)
    ├─ 🟡 Streaming Jobs (real-time)
    │  ├─ Event Aggregation
    │  ├─ Clickstream Analysis
    │  ├─ Data Enrichment
    │  └─ CDC Transformation
    ├─ 🟢 Batch Jobs (scheduled)
    │  ├─ Hourly Aggregates
    │  ├─ Daily Summaries
    │  └─ User Segmentation
    └─ 📊 Output Stores (Parquet, Delta, CSV)
```

---

## 🏗️ Architecture

### Directory Structure

```
processing_layer/
├── configs/                  # Configuration modules
│   ├── spark_config.py      # Spark session and job configuration
│   └── logging_config.py    # Centralized logging setup
├── jobs/                     # Processing jobs
│   ├── streaming/           # Real-time streaming jobs
│   │   ├── event_aggregation.py
│   │   ├── clickstream_analysis.py
│   │   ├── data_enrichment.py
│   │   └── cdc_transformation.py
│   └── batch/               # Batch processing jobs
│       ├── hourly_aggregate.py
│       ├── daily_summary.py
│       └── user_segmentation.py
├── utils/                    # Utility modules
│   ├── spark_utils.py       # Spark session factory, schemas
│   └── transformations.py   # Common data transformation functions
├── logs/                     # Application logs (JSON format)
├── outputs/                  # Data output directory
├── orchestrator.py          # Main orchestrator - manages all jobs
├── docker-compose.yml       # Spark cluster setup
├── Dockerfile               # Container for processing jobs
└── requirements.txt         # Python dependencies
```

---

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose (for containerized Spark)
- Python 3.11+
- PySpark 3.5.0+
- Apache Kafka (from ingestion_layer)

### Installation

1. **Install Python dependencies:**

```bash
cd /workspaces/Data-Platform/processing_layer
pip install -r requirements.txt
```

2. **Configure environment variables (optional):**

```bash
export KAFKA_BOOTSTRAP_SERVER=localhost:29092
export SPARK_MASTER=local[*]  # or spark://spark-master:7077 for cluster
export LOG_LEVEL=INFO
export CHECKPOINT_DIR=/tmp/spark-checkpoints
export OUTPUTS_DIR=/workspaces/Data-Platform/processing_layer/outputs
```

3. **Start Spark cluster (Docker):**

```bash
docker-compose -p data-platform up -d
```

This starts:
- Spark Master (port 8080)
- Spark Worker 1 (port 8081)
- Spark Worker 2 (port 8082)
- Processing Orchestrator (optional)

---

## 📡 Streaming Jobs

Real-time processing of incoming Kafka events with ~10-second micro-batch intervals.

### 1. Event Aggregation

**Purpose:** Real-time counting and aggregation of application events

**Input:** `topic_app_events`

**Processing:**
- Aggregate events by user, event type, app type in 1-minute windows
- Calculate event counts per window
- Collect session IDs for each aggregation

**Output:** Parquet files in `outputs/events_aggregated_realtime/`

**Run individually:**
```bash
python jobs/streaming/event_aggregation.py
```

---

### 2. Clickstream Analysis

**Purpose:** Real-time user journey and click path analysis

**Input:** `topic_clickstream`

**Processing:**
- Track sequential clicks per session
- Calculate session metrics (duration, unique pages, click count)
- Identify page navigation paths

**Output:** Parquet files in `outputs/clickstream_sessions/`

**Run individually:**
```bash
python jobs/streaming/clickstream_analysis.py
```

---

### 3. Data Enrichment

**Purpose:** Enhance raw events with additional context (user attributes, device info)

**Input:** All Kafka topics

**Processing:**
- Join events with user master data
- Enrich with device/location information
- Add calculated fields (engagement score, risk flags)

**Output:** Enriched event streams to Kafka or Parquet

---

### 4. CDC Transformation

**Purpose:** Transform PostgreSQL CDC events into standardized operations

**Input:** `topic_cdc_changes`

**Processing:**
- Parse Debezium CDC format
- Classify operations (INSERT, UPDATE, DELETE)
- Extract before/after record states
- Calculate operation summaries per table

**Output:** Parquet files in `outputs/cdc_transformed/`

**Run individually:**
```bash
python jobs/streaming/cdc_transformation.py
```

---

## 🟢 Batch Jobs

Scheduled jobs that run periodically for analytical processing.

### 1. Hourly Aggregates

**Purpose:** Hourly rollup of all events and metrics

**Schedule:** Every hour (configurable)

**Processing:**
- Read streaming outputs (events aggregated in real-time)
- Group by hour + dimensions (event_type, app_type)
- Calculate totals and metrics

**Output:** `outputs/hourly_aggregates/`

**Run manually:**
```bash
python jobs/batch/hourly_aggregate.py --target-hour "2026-02-16 14:00:00"
```

---

### 2. Daily Summaries

**Purpose:** Daily KPI metrics and summary statistics

**Schedule:** Daily (configurable - default 2 AM)

**Processing:**
- Aggregate metrics from hourly data
- Calculate daily KPIs (total events, session count, etc.)
- Compute percentiles (p95 session duration, etc.)

**Output:** `outputs/daily_summaries/`

**Run manually:**
```bash
python jobs/batch/daily_summary.py --target-date "2026-02-16"
```

---

### 3. User Segmentation

**Purpose:** User profiling and behavioral segmentation

**Schedule:** Daily (configurable)

**Segments:**
- **VIP**: High engagement (score > 100)
- **Active**: Medium engagement (score 50-100)
- **Regular**: Low engagement (score 20-50)
- **Inactive**: Minimal engagement (score < 20)

**Dimensions:**
- Session frequency (Very High, High, Medium, Low)
- Content interest (Diverse, Selected, Limited)
- Device preference (Multi-device, Single-device)

**Output:** `outputs/user_segments/` (Parquet with segment assignments)

**Run manually:**
```bash
python jobs/batch/user_segmentation.py --lookback-days 30
```

---

## 🎛️ Configuration

### Spark Settings (`configs/spark_config.py`)

```python
# Memory allocation
EXECUTOR_MEMORY = "2g"           # Per executor
DRIVER_MEMORY = "2g"             # Driver process
EXECUTOR_CORES = 2               # Cores per executor

# Streaming
STREAMING_BATCH_INTERVAL_MS = 10000   # 10-second batches
STREAMING_MAX_OFFSETS_PER_TRIGGER = 10000

# Checkpoint & Output
CHECKPOINT_DIR = "/tmp/spark-checkpoints"
OUTPUTS_DIR = "/path/to/outputs"
```

### Kafka Consumer Settings

```python
KAFKA_BOOTSTRAP_SERVER = "localhost:29092"
KAFKA_CONSUMER_CONFIG = {
    "auto.offset.reset": "latest",      # Start from latest for streaming
    "maxOffsetsPerTrigger": 10000,       # Rate limiting
    "failOnDataLoss": False              # Resilience
}
```

### Job Configuration (`configs/spark_config.py`)

Enable/disable jobs:
```python
PROCESSING_JOBS = {
    "event_aggregation": {
        "type": "streaming",
        "enabled": True,
        "description": "Real-time event aggregation"
    },
    # ... more jobs
}
```

---

## 💾 Output Data

### Streaming Outputs (Real-time, Append Mode)

All streaming job outputs use **append-mode Parquet** for ACID compliance:

```
outputs/
├── events_aggregated_realtime/       # Event counts by window
├── clickstream_sessions/              # Session + path analysis
├── enriched_events/                   # Enriched events from all sources
└── cdc_transformed/                   # Transformed CDC operations
```

**Example schema (events_aggregated_realtime):**
```
window_start: timestamp
window_end: timestamp
user_id: string
event_type: string (page_view, click, purchase, scroll, search)
app_type: string (mobile, web, api)
event_count: integer
session_ids: array<string>
processing_time: timestamp
```

### Batch Outputs (Analytical)

```
outputs/
├── hourly_aggregates/                # Hourly rollups
├── daily_summaries/                  # Daily KPIs
└── user_segments/                    # User profiles & segments
```

---

## 🚦 Running Jobs

### Start All Services

```bash
# Start Spark cluster + orchestrator
docker-compose -p data-platform up -d

# Check status
docker-compose -p data-platform ps

# View Spark Master UI
# Open browser: http://localhost:8080
```

### Run Orchestrator (Local)

```bash
# Start with both streaming and batch jobs
python orchestrator.py

# Start with only streaming
python orchestrator.py --streaming True --batch False

# Start with only batch
python orchestrator.py --streaming False --batch True
```

### Run Individual Jobs

**Streaming jobs (continuous):**
```bash
python jobs/streaming/event_aggregation.py
python jobs/streaming/clickstream_analysis.py
python jobs/streaming/cdc_transformation.py
```

**Batch jobs (one-time execution):**
```bash
python jobs/batch/hourly_aggregate.py --target-hour "2026-02-16 14:00:00"
python jobs/batch/daily_summary.py --target-date "2026-02-16"
python jobs/batch/user_segmentation.py --lookback-days 30
```

### Monitor Spark

```bash
# Spark Master Web UI
http://localhost:8080

# Driver Application UI (while job running)
http://localhost:4040

# Check logs
tail -f logs/event_aggregation.log
tail -f logs/orchestrator.log
```

---

## 🔧 Development Guide

### Adding a New Streaming Job

1. **Create job file** in `jobs/streaming/my_job.py`:

```python
from utils.spark_utils import create_spark_session, read_kafka_stream, write_parquet_stream

class MyStreamingJob:
    def __init__(self):
        self.spark = create_spark_session("my-job")
        self.query = None
    
    def start(self):
        # Read from Kafka
        df = read_kafka_stream(
            self.spark,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVER,
            topics=["my_topic"],
            group_id="my-consumer-group"
        )
        
        # Transform
        transformed = df.filter(...).select(...)
        
        # Write output
        self.query = write_parquet_stream(
            transformed,
            output_path="/path/to/output",
            checkpoint_dir="/path/to/checkpoint"
        )
        
        self.query.awaitTermination()
    
    def stop(self):
        if self.query:
            self.query.stop()
        if self.spark:
            self.spark.stop()
```

2. **Add to orchestrator** in `orchestrator.py`:

```python
PROCESSING_JOBS["my_job"] = {
    "type": "streaming",
    "enabled": True,
    "description": "My custom streaming job"
}

# In orchestrator's module_map:
module_map["my_job"] = "jobs.streaming.my_job"
```

### Using Transformations

```python
from utils.transformations import DataTransformations as DT

# Parse JSON
df = DT.parse_kafka_value_json(df)

# Add timestamp
df = DT.add_processing_timestamp(df)

# Window operations
df = DT.add_window_time(df, "timestamp", "1 minute")

# Aggregation
df = DT.aggregate_by_user_window(df, window_duration="1 hour")

# Clean data
df = DT.filter_valid_records(df)
df = DT.remove_duplicates(df, ["user_id", "event_id"])
```

---

## 📊 Example Analytics Workflows

### User Engagement Analysis

```python
# Get high-engagement users in last 7 days
from pyspark.sql.functions import col, date_sub, current_date

engaged_users = user_segments.filter(
    col("user_segment").isin(["VIP", "Active"]),
    col("processing_time") > date_sub(current_date(), 7)
)

engaged_users.write.parquet("outputs/engaged_users_7d")
```

### Hourly Event Trends

```python
hourly_events = spark.read.parquet("outputs/hourly_aggregates")
                          .groupBy("hour", "event_type")
                          .agg(F.sum("event_count").alias("total"))

hourly_events.write.parquet("outputs/event_trends")
```

### Session Quality Score

```python
sessions = spark.read.parquet("outputs/clickstream_sessions")

quality_df = sessions.withColumn("quality_score",
    F.when(col("session_duration_sec") > 300, 5)
     .when(col("session_duration_sec") > 60, 4)
     .when(col("session_duration_sec") > 10, 3)
     .otherwise(1)
)

quality_df.write.parquet("outputs/session_quality")
```

---

## 🐛 Troubleshooting

### Streaming Job Hangs

**Issue:** Job doesn't process data

**Solutions:**
1. Check Kafka connectivity: `kafka-topics --bootstrap-server localhost:29092 --list`
2. Verify spark master is running: `http://localhost:8080`
3. Check logs: `tail -f logs/event_aggregation.log`
4. Ensure checkpoint directory exists and is writable

### Out of Memory

**Issue:** `java.lang.OutOfMemoryError`

**Solutions:**
```bash
# Increase executor memory
export EXECUTOR_MEMORY=4g

# Reduce batch size
STREAMING_MAX_OFFSETS_PER_TRIGGER = 5000
```

### Checkpoint Corruption

**Issue:** Job fails with "incompatible checkpoint"

**Solutions:**
```bash
# Delete corrupted checkpoint and restart
rm -rf /tmp/spark-checkpoints/event_aggregation/*
python jobs/streaming/event_aggregation.py
```

### No Data Output

**Issue:** Streaming job runs but no output files

**Solutions:**
1. Verify Kafka topic has messages: `kafka-console-consumer --bootstrap-server localhost:29092 --topic topic_app_events --from-beginning`
2. Check if streaming micro-batch has data: Add console output in job
3. Ensure output path is writable: `ls -la /workspaces/Data-Platform/processing_layer/outputs/`

---

## 📈 Performance Tuning

### Optimize Streaming

```python
# Increase parallelism
spark.sql.shuffle.partitions = 200
spark.default.parallelism = 200

# Enable adaptive query execution
spark.sql.adaptive.enabled = true

# Backpressure handling
spark.streaming.backpressure.enabled = true
spark.streaming.backpressure.initialRate = 100000
```

### Optimize Batch

```python
# Enable bucketing for frequent joins
df.bucketBy(100, "user_id").sortBy("timestamp").write.parquet(...)

# Partition output data
df.write.partitionBy("date", "hour").parquet(...)

# Coalesce partitions before write
df.coalesce(10).write.parquet(...)
```

---

## 📝 Monitoring & Alerts

### Key Metrics to Monitor

- **Throughput**: events/second processed
- **Latency**: end-to-end processing latency
- **Backlog**: pending events in Kafka queue
- **CPU/Memory**: Spark executor resource utilization
- **Failed Jobs**: Number of failed microbatches or batch jobs

### Log Aggregation

Logs are written to:
- Console (real-time, colored)
- JSON files (machine-readable, for ELK/Splunk)
- Location: `logs/` directory

```bash
# View last 100 lines of event aggregation logs
tail -100 logs/event_aggregation.log | jq .

# Search for errors
grep ERROR logs/*.log
```

---

## 🔄 CI/CD Integration

### Unit Test Job

```bash
# For test environment
export SPARK_MASTER=local[2]
export KAFKA_BOOTSTRAP_SERVER=localhost:29092

python jobs/streaming/event_aggregation.py --test-mode
```

### Health Check

```bash
# Check if Spark cluster is healthy
curl http://localhost:8080/api/v1/applications

# Check if orchestrator is running
curl http://localhost:9999/health
```

---

## 📚 References

- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Spark Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Kafka Integration](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html)
- [PySpark API](https://spark.apache.org/docs/latest/api/python/)

---

## 📝 License

Part of Data-Platform project. See main README for details.

---

**Last Updated:** February 2026  
**Version:** 1.0.0
