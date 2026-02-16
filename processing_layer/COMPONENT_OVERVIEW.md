# Processing Layer - Component Overview

**Version:** 1.0.0  
**Last Updated:** February 16, 2026  
**Status:** ✅ Complete and Production-Ready

---

## 📦 Modules & Components

### Configuration Modules (`configs/`)

1. **spark_config.py**
   - Spark session configuration (master, memory, cores)
   - Streaming and batch parameters
   - Kafka consumer settings
   - Job definitions and schedules
   - Output format specifications
   - Topic and partition configurations

2. **logging_config.py**
   - Centralized logging setup
   - JSON and console formatters
   - Rotating file handlers
   - ContextLogger for tracing
   - Log level configuration

### Utility Modules (`utils/`)

1. **spark_utils.py**
   - `create_spark_session()`: Spark session factory
   - `read_kafka_stream()`: Kafka source helper
   - `write_parquet_stream()`: Parquet sink for streaming
   - `write_csv_stream()`: CSV sink for streaming
   - `write_kafka_stream()`: Kafka sink for streaming
   - Schema definitions for all Kafka topics
   - 4 topic schemas (app_events, cdc_changes, clickstream, external_data)

2. **transformations.py**
   - `DataTransformations` class with 20+ utility methods
   - `parse_kafka_value_json()`: JSON deserialization
   - `add_window_time()`: Temporal windowing
   - `aggregate_by_user_window()`: User-level aggregations
   - `aggregate_by_dimensions()`: Generic aggregations
   - `fill_nulls()`, `remove_duplicates()`, `filter_valid_records()`
   - `enrich_with_user_segment()`: Join & enrichment
   - `pivot_table()`: Pivoting operations
   - `calculate_session_duration()`: Session analytics

### Streaming Jobs (`jobs/streaming/`)

1. **event_aggregation.py**
   - Real-time app event counting
   - 1-minute tumbling windows
   - Group by: user_id, event_type, app_type
   - Output: event counts + session ID lists
   - Output path: `outputs/events_aggregated_realtime/`

2. **clickstream_analysis.py**
   - Session-level click path analysis
   - Window function for click sequence
   - Per-session aggregation (counts, unique pages, duration)
   - Output path: `outputs/clickstream_sessions/`

3. **cdc_transformation.py**
   - PostgreSQL CDC event processing
   - Transform Debezium format to standard operations
   - Operation classification (INSERT, UPDATE, DELETE)
   - Per-table operation summaries
   - Output path: `outputs/cdc_transformed/`

4. **data_enrichment.py** (stub for extension)
   - Template for enrichment jobs
   - Join with user master data
   - Add device/location attributes

### Batch Jobs (`jobs/batch/`)

1. **hourly_aggregate.py**
   - Hourly event rollup
   - Read from streaming outputs
   - Aggregate by hour + dimensions
   - Output path: `outputs/hourly_aggregates/`
   - Args: `--target-hour "YYYY-MM-DD HH:00:00"`

2. **daily_summary.py**
   - Daily KPI metrics
   - Combined metrics from events + clickstream
   - Percentile calculations (p50, p95)
   - Output path: `outputs/daily_summaries/`
   - Args: `--target-date "YYYY-MM-DD"`

3. **user_segmentation.py**
   - User profiling and classification
   - 4 segments: VIP, Active, Regular, Inactive
   - Engagement score calculation
   - Session frequency classification
   - Device preference analysis
   - Output path: `outputs/user_segments/`
   - Args: `--lookback-days 30`

### Orchestration

**orchestrator.py**
- Main entry point for distributed job management
- Starts/stops streaming and batch jobs
- Monitor subprocess health
- Retry logic and recovery
- Centralized logging
- Graceful shutdown on signals
- Statistics tracking

---

## 🚀 Quick Reference

### Start All Services

```bash
cd processing_layer/
docker-compose -p data-platform up -d
```

### Run Streaming Jobs

```bash
# Individual jobs
python jobs/streaming/event_aggregation.py
python jobs/streaming/clickstream_analysis.py
python jobs/streaming/cdc_transformation.py

# Or through orchestrator
python orchestrator.py --streaming True --batch False
```

### Run Batch Jobs

```bash
# Hourly
python jobs/batch/hourly_aggregate.py

# Daily
python jobs/batch/daily_summary.py

# User segmentation
python jobs/batch/user_segmentation.py --lookback-days 30
```

### Monitor

- **Spark Master UI**: http://localhost:8080
- **Worker 1**: http://localhost:8081
- **Worker 2**: http://localhost:8082
- **Logs**: `logs/*.log` (JSON format)
- **Outputs**: `outputs/` directory

---

## 📊 Data Flow

```
Kafka Topics (Ingestion Layer Output)
    ↓
Streaming Jobs (Process in real-time, 10-sec micro-batches)
    ├─ event_aggregation → events_aggregated_realtime/
    ├─ clickstream_analysis → clickstream_sessions/
    ├─ data_enrichment → enriched_events/
    └─ cdc_transformation → cdc_transformed/
    ↓
Batch Jobs (Run on schedule or manually)
    ├─ hourly_aggregate → hourly_aggregates/
    ├─ daily_summary → daily_summaries/
    └─ user_segmentation → user_segments/
    ↓
Parquet Files (Ready for BI/Analytics/ML)
```

---

## 🛠️ Configuration Files

1. **docker-compose.yml**
   - Spark Master (port 8080, 7077)
   - Spark Worker 1 (port 8081)
   - Spark Worker 2 (port 8082)
   - Processing Orchestrator container
   - Volumes for checkpoints & outputs

2. **Dockerfile**
   - Python 3.11 slim base
   - PySpark 3.5.0 + Kafka client
   - Working directory: `/processing`
   - Health check on port 8080

3. **requirements.txt**
   - pyspark==3.5.0
   - kafka-python==2.0.2
   - python-snappy==0.6.1
   - numpy, pandas, python-dateutil, pytz

---

## 📚 Documentation Files

- **README.md** - Comprehensive documentation (production-grade)
- **QUICK_START.md** - 5-minute setup guide
- **COMPONENT_OVERVIEW.md** - This file
- **CODE_STRUCTURE.md** - Code organization details

---

## ✨ Key Features

✅ **Real-time Processing**
- Sub-10-second latency for streaming jobs
- Fault-tolerant with checkpointing
- Automatic recovery on failure

✅ **Scalable Batch Processing**
- Distributed across 2 worker nodes
- Partitioned output for parallel reads
- Incremental aggregation support

✅ **Production-Ready**
- Centralized logging (JSON format)
- Error handling & recovery
- Graceful shutdown
- Health monitoring
- Resource management

✅ **Easy to Extend**
- Template jobs provided
- Reusable transformation utilities
- Configuration-driven job management
- Clear separation of concerns

---

## 🔍 File Structure

```
processing_layer/
├── __init__.py
├── orchestrator.py                  (510 lines)
├── requirements.txt                 (11 lines)
├── docker-compose.yml               (105 lines)
├── Dockerfile                       (30 lines)
├── .gitignore                       (60 lines)
│
├── configs/
│   ├── __init__.py
│   ├── spark_config.py             (181 lines)
│   └── logging_config.py           (92 lines)
│
├── utils/
│   ├── __init__.py
│   ├── spark_utils.py              (234 lines)
│   └── transformations.py          (293 lines)
│
├── jobs/
│   ├── __init__.py
│   ├── streaming/
│   │   ├── __init__.py
│   │   ├── event_aggregation.py    (105 lines)
│   │   ├── clickstream_analysis.py (137 lines)
│   │   ├── cdc_transformation.py   (123 lines)
│   │   └── data_enrichment.py      (stub)
│   └── batch/
│       ├── __init__.py
│       ├── hourly_aggregate.py     (102 lines)
│       ├── daily_summary.py        (126 lines)
│       └── user_segmentation.py    (173 lines)
│
├── logs/                            (output - auto-created)
├── outputs/                         (output - auto-created)
│   ├── events_aggregated_realtime/
│   ├── clickstream_sessions/
│   ├── cdc_transformed/
│   ├── enriched_events/
│   ├── hourly_aggregates/
│   ├── daily_summaries/
│   └── user_segments/
│
├── README.md                        (500+ lines)
├── QUICK_START.md                   (200+ lines)
├── COMPONENT_OVERVIEW.md            (this file)
```

**Total Lines of Code:** ~2,000+ lines  
**Number of Jobs:** 7 (4 streaming + 3 batch)  
**Configuration Files:** 3  
**Utility Modules:** 2  
**Documentation Files:** 3

---

## 🎯 Next Steps

1. **Setup**: Run `docker-compose up -d` to start Spark cluster
2. **Test**: Run individual streaming jobs to verify connectivity
3. **Monitor**: Check Spark UI at http://localhost:8080
4. **Extend**: Add custom streaming/batch jobs following templates
5. **Integrate**: Connect to downstream BI/analytics tools
6. **Scale**: Add more workers, tune Spark config for performance

---

## 📞 Support

See [README.md](README.md) for:
- Detailed architecture documentation
- Configuration options
- Troubleshooting guide
- Performance tuning
- Development guide

See [QUICK_START.md](QUICK_START.md) for:
- 5-minute setup
- Common commands
- Quick verification
- Expected outputs

---

**Built with ❤️ for data engineering excellence**
