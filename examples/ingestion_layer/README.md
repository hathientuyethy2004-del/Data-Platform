# 🔄 INGESTION LAYER - Hướng Dẫn Hoàn Chỉnh

## 📋 Mục Lục

1. [Giới Thiệu](#giới-thiệu)
2. [Kiến Trúc](#kiến-trúc)
3. [Cài Đặt](#cài-đặt)
4. [Chạy Hệ Thống](#chạy-hệ-thống)
5. [Cấu Hình](#cấu-hình)
6. [Giám Sát & Metrics](#giám-sát--metrics)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Giới Thiệu

**INGESTION LAYER** là lớp tiếp nhận dữ liệu (data consumption) từ Kafka brokers. Lớp này:

- **Consume dữ liệu** từ 4 Kafka topics (App Events, CDC Changes, Clickstream, External Data)
- **Validate dữ liệu** theo schema rules định sẵn
- **Monitor hiệu suất** (throughput, latency, error rate)
- **Xử lý lỗi** với Dead Letter Queue
- **Tính metrics** và health check real-time

### 🏗️ Mối Quan Hệ Với Các Lớp

```
┌──────────────────────────────┐
│   DATA SOURCES LAYER         │  (simulations/)
│   - Mobile/Web Simulators    │
│   - CDC Simulator            │
│   - Clickstream Simulator    │
│   - External Data Simulator  │
└────────────┬─────────────────┘
             │ (produces data)
             ↓
┌──────────────────────────────┐
│   KAFKA CLUSTER              │  (7.5.0)
│   - 4 Topics                 │
│   - Schema Registry          │
│   - KafkaUI Monitoring       │
└────────────┬─────────────────┘
             │ (consume data)
             ↓
┌──────────────────────────────┐
│   INGESTION LAYER ✨         │  (ingestion_layer/)
│   - 5 Consumer Groups        │ ← YOU ARE HERE
│   - Data Validators          │
│   - Metrics Collector        │
│   - Health Checker           │
└──────────────────────────────┘
             │ (processed data)
             ↓
     (Processing Layer)
     (Storage Layer)
```

---

## 🏗️ Kiến Trúc

### Component 1: Kafka Configuration (`configs/kafka_config.py`)

```python
# Consumer groups được support
CONSUMER_GROUPS = {
    "app_events_consumer": ["topic_app_events"],
    "cdc_consumer": ["topic_cdc_changes"],
    "clickstream_consumer": ["topic_clickstream"],
    "external_data_consumer": ["topic_external_data"],
    "unified_consumer": ["topic_app_events", "topic_cdc_changes", ...]
}

# Validation rules cho mỗi topic
VALIDATION_RULES = {
    "topic_app_events": {
        "required_fields": ["event_type", "user_id", "session_id", ...]
    }
}
```

### Component 2: Kafka Consumer (`consumers/kafka_consumer.py`)

```python
class KafkaIngestionConsumer:
    # Consume tin nhắn từ Kafka
    # Batch processing
    # Error handling
    # Metrics tracking
```

**Tính năng:**
- Consume theo batch (configurable batch size)
- Automatic offset management
- Error recovery với retry logic
- Per-topic message buffering

### Component 3: Data Validator (`validation/data_validator.py`)

```python
class DataValidator:
    # Validate tin nhắn theo schema
    # Check required fields
    # Type validation
    # Business rule constraints
    # Timestamp validation
```

**Validation Rules:**

```python
topic_app_events:
    required: event_type, user_id, session_id, timestamp
    constraints: event_type in ['page_view', 'click', 'purchase']

topic_cdc_changes:
    required: op, table, before, after, ts_ms
    constraints: op in ['i', 'u', 'd']

topic_clickstream:
    required: event_id, user_id, page_url, timestamp
    constraints: device_type in ['desktop', 'mobile', 'tablet']

topic_external_data:
    required: data_source, timestamp
    constraints: data_source in ['weather', 'maps', 'social_media']
```

### Component 4: Metrics Collector (`monitoring/metrics.py`)

```python
class MetricsCollector:
    # Collect metrics
    # Calculate throughput (msgs/sec)
    # Calculate latency (min/avg/max/p95/p99)
    # Track error rates
    # Monitor message sizes

class HealthCheck:
    # Check error rate
    # Check latency
    # Check throughput
    # Overall system health status
```

### Component 5: Orchestrator (`orchestrator.py`)

```python
class IngestionLayerOrchestrator:
    # Quản lý multiple consumer groups
    # Khởi động/dừng các consumers
    # Giám sát tất cả
    # Graceful shutdown
```

---

## 📦 Cài Đặt

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (nếu chạy locally)
- DATA SOURCES LAYER đang chạy (`simulations/`)
- Kafka cluster đang sẵn sàng

### Bước 1: Clone/Setup Repository

```bash
cd /workspaces/Data-Platform/ingestion_layer
```

### Bước 2: Install Dependencies (Local)

```bash
pip install -r requirements.txt
```

### Bước 3: Kiểm Tra Kafka Connectivity

```bash
# Verify Kafka is accessible
docker exec kafka kafka-broker-api-versions --bootstrap-server kafka:9092
```

---

## 🚀 Chạy Hệ Thống

### Option 1: Chạy Với Docker Compose

#### Từ DATA SOURCES LAYER đang chạy

```bash
# Make sure simulations are running
cd /workspaces/Data-Platform/simulations
docker-compose -f docker-compose-production.yml up -d

# Verify kafka is healthy
docker ps | grep kafka
```

#### Chạy INGESTION LAYER

```bash
cd /workspaces/Data-Platform/ingestion_layer

# Build images
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f

# View specific consumer
docker logs ingestion-app-events -f
docker logs ingestion-unified -f
```

### Option 2: Chạy Locally (Python)

```bash
# Terminal 1: Chạy Orchestrator
cd /workspaces/Data-Platform/ingestion_layer
python orchestrator.py

# Sẽ output:
# ======= STARTING INGESTION LAYER =======
# 📌 Initializing consumer group: app_events_consumer
# ✅ Initialized 5/5 consumer groups
# 📊 Starting consumption...
```

### Option 3: Chạy Individual Consumer

```bash
cd /workspaces/Data-Platform/ingestion_layer

python -c "
from consumers.kafka_consumer import create_consumer
consumer = create_consumer('app_events_consumer', ['topic_app_events'])
consumer.consume_messages(timeout_sec=30)
"
```

---

## ⚙️ Cấu Hình

### Config Files Location

```
ingestion_layer/
├── configs/
│   └── kafka_config.py          # Main configuration
├── .env                         # Environment variables (optional)
└── docker-compose.yml           # Docker configuration
```

### Key Configuration Variables

```python
# kafka_config.py

# Kafka Connection
KAFKA_BOOTSTRAP_SERVER = "kafka:9092"

# Consumer Settings
CONSUMER_CONFIG = {
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True,
    "max.poll.records": 500,
    "session.timeout.ms": 30000
}

# Ingestion Settings
INGESTION_CONFIG = {
    "batch_size": 100,
    "batch_timeout_ms": 5000,
    "retry_attempts": 3,
    "enable_validation": True,
    "enable_monitoring": True
}

# Monitoring
MONITORING_CONFIG = {
    "metrics_interval_sec": 10,
    "log_interval_sec": 30,
    "enable_prometheus": True,
    "prometheus_port": 8001
}
```

### Environment Variables (Optional)

```bash
# Create .env file
cat > /workspaces/Data-Platform/ingestion_layer/.env << 'EOF'
KAFKA_BROKERS=kafka:9092
KAFKA_BOOTSTRAP_SERVER=kafka:9092
SCHEMA_REGISTRY_URL=http://schema-registry:8081
LOG_LEVEL=INFO
CONSUMER_BATCH_SIZE=100
CONSUMER_TIMEOUT_MS=5000
ENABLE_VALIDATION=true
ENABLE_MONITORING=true
EOF

# Load variables
source .env
```

---

## 📊 Giám Sát & Metrics

### Real-Time Metrics

Mỗi 10 giây, orchestrator in ra metrics:

```
📊 INGESTION LAYER METRICS:
Timestamp: 2026-02-16T12:30:00.000Z

⚡ Throughput (messages/sec):
  overall_msgs_per_sec: 42.5
  topic_app_events_msgs_per_sec: 20.3
  topic_cdc_changes_msgs_per_sec: 8.2
  topic_clickstream_msgs_per_sec: 13.0
  topic_external_data_msgs_per_sec: 0.0

⏱️ Latency (ms):
  latency_min_ms: 2.1
  latency_avg_ms: 5.7
  latency_max_ms: 45.3
  latency_p95_ms: 12.4
  latency_p99_ms: 38.2

❌ Error Rate:
  total_metrics: 500
  error_count: 2
  error_rate_percent: 0.4%

📦 Message Size (bytes):
  total_size_bytes: 512000
  total_size_mb: 0.49
  avg_message_size_bytes: 1024
```

### Health Check

```
❤️ HEALTH CHECK: HEALTHY
Summary: 3 checks, 0 unhealthy, 0 warnings

✅ error_rate: Error rate: 0.40%
✅ latency: Max latency: 45ms, Avg: 5.70ms
✅ throughput: Throughput: 42.50 msgs/sec
```

### View Logs

```bash
# All logs
docker-compose logs

# Specific consumer logs
docker-compose logs ingestion-app-events

# Follow logs
docker-compose logs -f ingestion-unified

# Filter logs
docker-compose logs | grep "ERROR"
docker-compose logs | grep "Validation"
```

### Monitor Using Kafka UI

**Kafka UI**: http://localhost:8080

Topics được giám sát:
- `topic_app_events` - User events
- `topic_cdc_changes` - Database changes
- `topic_clickstream` - Navigation events
- `topic_external_data` - External sources

---

## 🧪 Testing & Validation

### Test 1: Kiểm Tra Consumer Connectivity

```bash
cd /workspaces/Data-Platform/ingestion_layer

python -c "
from configs.kafka_config import KAFKA_BOOTSTRAP_SERVER, validate_config
import sys

if validate_config():
    print('✅ Configuration valid')
    print(f'Kafka Bootstrap: {KAFKA_BOOTSTRAP_SERVER}')
    sys.exit(0)
else:
    print('❌ Configuration invalid')
    sys.exit(1)
"
```

### Test 2: Validate Data Validator

```bash
python validation/data_validator.py
# Output:
# Topic: topic_app_events
# Valid: True
# Errors: []
# Checks: 1/1
```

### Test 3: Validate Metrics

```bash
python monitoring/metrics.py
# Output:
# 📊 INGESTION LAYER METRICS:
# ⚡ Throughput...
# ⏱️ Latency...
```

### Test 4: Run Single Consumer

```bash
cd /workspaces/Data-Platform/ingestion_layer
timeout 30 python consumers/kafka_consumer.py
```

---

## 📈 Performance Tuning

### Optimize for High Throughput

```python
# kafka_config.py
CONSUMER_CONFIG = {
    "max.poll.records": 1000,      # Increase batch size
    "fetch.min.bytes": 10240,      # 10KB minimum
    "fetch.max.wait.ms": 1000,     # Wait up to 1 second
}

INGESTION_CONFIG = {
    "batch_size": 500,             # Larger batch
    "enable_validation": False,    # Disable validation if not needed
}
```

### Optimize for Low Latency

```python
CONSUMER_CONFIG = {
    "max.poll.records": 10,        # Small batch
    "fetch.min.bytes": 1,          # Process immediately
    "fetch.max.wait.ms": 100,      # Minimal wait
}

INGESTION_CONFIG = {
    "batch_size": 10,              # Small batch
}
```

---

## 🔍 Troubleshooting

### Problem 1: Consumer Lag

**Symptom:**
```
Consumer lag: 50000 messages
```

**Solution:**
```python
# Increase batch size
INGESTION_CONFIG["batch_size"] = 500  # From 100

# Increase max.poll.records
CONSUMER_CONFIG["max.poll.records"] = 1000
```

### Problem 2: High Latency

**Symptom:**
```
latency_max_ms: 5000
```

**Solution:**
```python
# Disable expensive operations
INGESTION_CONFIG["enable_validation"] = False

# Use simpler consumer config
CONSUMER_CONFIG = {
    "fetch.min.bytes": 1024,
    "fetch.max.wait.ms": 100
}
```

### Problem 3: Validation Failures

**Symptom:**
```
Validation failed: Missing required field: user_id
```

**Solution:**
```python
# Check schema definition
# Update VALIDATION_RULES in kafka_config.py

# Or disable validation temporarily
INGESTION_CONFIG["enable_validation"] = False
```

### Problem 4: Cannot Connect to Kafka

**Symptom:**
```
❌ Failed to initialize consumer: [NoBrokersAvailable]
```

**Solution:**
```bash
# Verify Kafka is running
docker ps | grep kafka

# Check Kafka is healthy
docker ps kafka

# Test connectivity
docker exec kafka kafka-broker-api-versions --bootstrap-server kafka:9092

# Check network
docker network ls
docker network inspect simulations_data-platform
```

### Problem 5: Out of Memory

**Symptom:**
```
MemoryError: Unable to allocate X GiB
```

**Solution:**
```python
# Reduce batch size
INGESTION_CONFIG["batch_size"] = 50  # From 100

# Disable metrics collection
MONITORING_CONFIG["enable_prometheus"] = False

# Clear logs periodically
rm -f /tmp/ingestion_checkpoints/*
```

---

## 📝 Docker Commands

### Build Images

```bash
cd /workspaces/Data-Platform/ingestion_layer
docker-compose build
```

### Start Services

```bash
docker-compose up -d
```

### View Logs

```bash
docker-compose logs -f ingestion-unified
```

### Stats

```bash
docker stats ingestion-app-events
```

### Stop Services

```bash
docker-compose down
```

### Clean Everything

```bash
docker-compose down -v
docker image rm $(docker images 'ingestion*' -q)
```

---

## 📚 Related Documentation

- [DATA SOURCES LAYER](../simulations/README.md)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Confluent Python Clients](https://docs.confluent.io/kafka-clients/python/current/overview.html)

---

## 🎯 Next Steps

1. **Processing Layer** - Transform & aggregate data
2. **Storage Layer** - Store processed data (Data Warehouse)
3. **Analytics Layer** - Build dashboards & reports

---

**Last Updated:** February 16, 2026  
**Version:** 1.0  
**Status:** ✅ Production Ready
