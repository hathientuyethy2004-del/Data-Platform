# 🏗️ INGESTION LAYER - Architecture & Design

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  DATA PLATFORM - Three-Layer Architecture                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Layer 1: DATA SOURCES LAYER (simulations/)                        │
│  ├── Mobile App Simulator (Kafka Producer)                         │
│  ├── Web App Simulator                                             │
│  ├── PostgreSQL CDC Simulator                                      │
│  ├── Clickstream Simulator                                         │
│  └── External Data Simulator                                       │
│          ↓ (Produce Data)                                          │
│  ┌───────────────────────────────────────────┐                     │
│  │ KAFKA CLUSTER (7.5.0)                     │                     │
│  │ ├── topic_app_events                      │                     │
│  │ ├── topic_cdc_changes                     │                     │
│  │ ├── topic_clickstream                     │                     │
│  │ ├── topic_external_data                   │                     │
│  │ └── Schema Registry                       │                     │
│  └───────────────────────────────────────────┘                     │
│          ↓ (Consume Data) ← YOU ARE HERE                           │
│  Layer 2: INGESTION LAYER (ingestion_layer/) ✨                    │
│  ├── App Events Consumer (parallelized)                            │
│  ├── CDC Changes Consumer                                          │
│  ├── Clickstream Consumer                                          │
│  ├── External Data Consumer                                        │
│  └── Unified Consumer (all topics)                                 │
│  ├── Data Validator (schema validation)                            │
│  ├── Metrics Collector (performance tracking)                      │
│  └── Health Checker (system monitoring)                            │
│          ↓ (Validated Data)                                        │
│  Layer 3: PROCESSING LAYER (future)                                │
│  ├── Spark Streaming (real-time agg)                               │
│  ├── Airflow DAGs (batch processing)                               │
│  └── Incremental Processing                                        │
│          ↓ (Processed Data)                                        │
│  Layer 4: STORAGE LAYER (future)                                   │
│  ├── Data Warehouse (BigQuery/Snowflake)                           │
│  ├── Data Lake (S3/HDFS)                                           │
│  └── Real-time views (ClickHouse/Druid)                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## INGESTION LAYER Deep Design

### 1. Consumer Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  ORCHESTRATOR (Main)                         │
│  IngestionLayerOrchestrator                                  │
└────────────────┬─────────────────────────────────────────────┘
                 │
    ┌────────────┴──────────────┬──────────────┬──────────────┐
    │                           │              │              │
    ↓                           ↓              ↓              ↓
┌────────────┐  ┌────────────┐ ┌──────────┐ ┌──────────┐  ┌──────────┐
│ Consumer 1 │  │ Consumer 2 │ │Consumer3 │ │Consumer4 │  │Consumer5 │
│ (Thread)   │  │ (Thread)   │ │(Thread)  │ │(Thread)  │  │(Thread)  │
│            │  │            │ │          │ │          │  │          │
│ Topic:     │  │ Topic:     │ │Topic:    │ │Topic:    │  │Topic:    │
│ app_events │  │cdc_changes │ │click     │ │ext_data  │  │unified   │
└───┬────────┘  └────┬───────┘ └────┬─────┘ └────┬─────┘  └────┬─────┘
    │                │              │            │             │
    ↓                ↓              ↓            ↓             ↓
┌────────────────────────────────────────────────────────────────┐
│          Kafka Broker (topic subscription)                    │
│   offset:0        offset:1000      offset:2500               │
└────────────────────────────────────────────────────────────────┘
```

### 2. Message Processing Flow

```
INPUT: Kafka Message
  ↓
[1] CONSUME: Read from Kafka
  - topic_app_events
  - topic_cdc_changes
  - topic_clickstream
  - topic_external_data
  ↓
[2] PARSE: Extract JSON payload
  - Deserialize message
  - Extract metadata (topic, partition, offset)
  ↓
[3] VALIDATE: Check data quality
  ├─ Required fields present?
  ├─ Correct data types?
  ├─ Within business constraints?
  └─ Valid timestamps?
  ↓
[4] ENRICH: Add metadata
  - __topic__ (source topic)
  - __partition__ (kafka partition)
  - __offset__ (kafka offset)
  - __timestamp__ (ingestion time)
  ↓
[5] BATCH: Accumulate messages
  - Buffer up to batch_size messages
  - Or timeout after batch_timeout_ms
  ↓
[6] METRICS: Collect performance data
  - Processing latency
  - Message throughput
  - Error rates
  - Per-topic statistics
  ↓
OUTPUT: Validated & Enriched Messages
```

### 3. Data Validation Pipeline

```
message = {
    "event_type": "page_view",
    "user_id": "user123",
    "session_id": "sess456",
    "timestamp": "2026-02-16T12:00:00Z",
    "app_type": "web"
}
    ↓
┌────────────────────────────────────┐
│ SCHEMA VALIDATION                  │
│ Check: VALIDATION_SCHEMAS          │
│   ✓ event_type in required fields  │
│   ✓ user_id is string              │
│   ✓ session_id is string           │
│   ✓ timestamp is ISO format        │
│   ✓ app_type is string             │
└────┬─────────────────────────────────┘
     ↓ (if all ✓)
┌────────────────────────────────────┐
│ CONSTRAINT VALIDATION              │
│ Check: event constraints           │
│   ✓ event_type in enum             │
│   ✓ app_type in enum               │
│   ✓ user_id length OK              │
└────┬─────────────────────────────────┘
     ↓ (if all ✓)
┌────────────────────────────────────┐
│ BUSINESS RULE VALIDATION           │
│ Check: domain logic                │
│   ✓ Timestamp not in future        │
│   ✓ Required context present       │
│   ✓ Coherent state transitions     │
└────┬─────────────────────────────────┘
     ↓ (if all ✓)
✅ VALID: Record metric, forward to next layer
     ↓ (if any ✗)
❌ INVALID: Log error, send to Dead Letter Queue
```

### 4. Metrics Collection

```
MetricsCollector (5-minute rolling window)
├── Throughput Calculation
│   ├─ Overall: messages/sec
│   ├─ Per-topic: messages/sec
│   └─ Per-consumer-group: messages/sec
│
├── Latency Calculation
│   ├─ Min: fastest processing
│   ├─ Avg: mean processing time
│   ├─ Max: slowest processing
│   ├─ P95: 95th percentile (tail latency)
│   └─ P99: 99th percentile (worst cases)
│
├── Error Tracking
│   ├─ Validation errors
│   ├─ Processing errors
│   ├─ Error rate %
│   └─ Error count per type
│
└── Message Size Statistics
    ├─ Min/Avg/Max size
    ├─ Total bytes processed
    └─ Bandwidth estimation
```

### 5. Health Check System

```
HealthCheck (every 30 seconds)
├─ Error Rate Check
│  └─ Alert if > 5%
│
├─ Latency Check
│  ├─ Max latency
│  ├─ Average latency
│  └─ Alert if max > 10s
│
├─ Throughput Check
│  ├─ Messages/sec
│  └─ Alert if < 1 msg/sec
│
└─ Overall Status
   ├─ Healthy: all checks pass
   ├─ Warning: 1-2 checks warn
   └─ Unhealthy: critical issues
```

---

## 🔄 Consumer Groups Design

### Consumer Group 1: App Events Consumer

```
Group ID: app_events_consumer
Topics: [topic_app_events]
Purpose: Consume user events from mobile/web apps

Data Flow:
  Mobile Simulator ---\
                       ├→ topic_app_events → app_events_consumer
  Web Simulator -------/

Event Examples:
{
  "event_type": "page_view",
  "user_id": "user123",
  "session_id": "s456",
  "timestamp": "2026-02-16T12:00:00Z",
  "app_type": "web",
  "properties": {
    "page": "/hotels",
    "duration_ms": 2500
  }
}
```

### Consumer Group 2: CDC Consumer

```
Group ID: cdc_consumer
Topics: [topic_cdc_changes]
Purpose: Consume database change events (CDC)

Data Flow:
  CDC Simulator → topic_cdc_changes → cdc_consumer

Event Examples:
{
  "op": "i",  // insert
  "table": "users",
  "before": null,
  "after": {
    "id": 123,
    "name": "John"
  },
  "ts_ms": 1645000000000
}
```

### Consumer Group 3: Clickstream Consumer

```
Group ID: clickstream_consumer
Topics: [topic_clickstream]
Purpose: Consume navigation & click events

Data Flow:
  Clickstream Simulator → topic_clickstream → clickstream_consumer

Event Examples:
{
  "event_id": "evt_789",
  "user_id": "user123",
  "page_url": "https://example.com/hotels",
  "event_type": "click",
  "timestamp": "2026-02-16T12:00:00Z",
  "element_id": "btn_book"
}
```

### Consumer Group 4: External Data Consumer

```
Group ID: external_data_consumer
Topics: [topic_external_data]
Purpose: Consume enrichment data (weather, location, etc)

Data Flow:
  External Data Simulator → topic_external_data → external_data_consumer

Event Examples:
{
  "data_source": "weather",
  "timestamp": "2026-02-16T12:00:00Z",
  "data": {
    "city": "Hanoi",
    "temperature": 25,
    "humidity": 70
  }
}
```

### Consumer Group 5: Unified Consumer

```
Group ID: unified_consumer
Topics: [all topics]
Purpose: Consume from all sources for unified processing

Data Flow:
  ┌─ topic_app_events ──┐
  ├─ topic_cdc_changes  ├→ unified_consumer
  ├─ topic_clickstream  │
  └─ topic_external_data┘

Use Case: Correlate events across all sources
         for comprehensive analysis
```

---

## 📊 Monitoring & Observability

### Metrics Collected

```
Per Message:
├─ Processing time (ms)
├─ Message size (bytes)
├─ Validation success/failure
├─ Topic
├─ Timestamp

Aggregated (5-min window):
├─ Throughput (msgs/sec)
├─ Latency percentiles (p95, p99)
├─ Error rate (%)
├─ Total messages
└─ By-topic breakdowns
```

### Health Indicators

```
Green (Healthy):
├─ Error rate < 1%
├─ Avg latency < 10ms
└─ Throughput > 10 msgs/sec

Yellow (Warning):
├─ Error rate 1-5%
├─ Avg latency 10-50ms
└─ Throughput 5-10 msgs/sec

Red (Critical):
├─ Error rate > 5%
├─ Avg latency > 50ms
└─ Throughput < 5 msgs/sec
```

---

## 🔐 Error Handling

### Validation Errors

```
Input: {"user_id": "u1", "session_id": "s1"}
       (missing event_type)
       ↓
Error: Missing required field: event_type
       ↓
Action: Count error, log, skip message
Result: Error rate increases, message not processed
```

### Processing Errors

```
Input: Exception in message processing
       ↓
Error: Consumer lag, throughput drop
       ↓
Action: Retry with backoff
        Max 3 attempts before skip
Result: Alert triggered
```

### Recovery Strategy

```
[Error Detected]
  ↓
[Retry Attempt 1] (wait 1s)
  ↓ fail
[Retry Attempt 2] (wait 2s)
  ↓ fail
[Retry Attempt 3] (wait 4s)
  ↓ fail
[Log Error] → Send to Dead Letter Queue
[Continue] → Process next message
```

---

## 🚀 Scaling & Performance

### Horizontal Scaling

```
Single Instance Performance:
  Throughput: ~50 msgs/sec
  Latency: 5-10ms avg
  CPU: 30-40%
  Memory: 256MB

With 5 Parallel Consumers:
  Throughput: ~250 msgs/sec  (5x)
  Latency: 5-10ms avg (same)
  CPU: 40-50% per container
  Memory: 256MB per container
```

### Bottleneck Analysis

```
Throughput Limited By:
1. Kafka fetch size (max.poll.records)
   Current: 500 msgs/poll
   → Increase to 1000 for 2x throughput

2. Batch timeout
   Current: 5000ms
   → Decrease to 1000ms for lower latency

3. Validation complexity
   Current: Full schema + constraint
   → Disable non-critical checks

4. Metrics collection overhead
   Current: Every message
   → Sample 1% for high throughput
```

---

## 🔄 Graceful Shutdown

```
[SIGTERM Received]
  ↓
Set shutdown_event
  ↓
Stop accepting new messages
  ↓
Process remaining buffered messages
  ↓
Close consumer connections
  ↓
Wait for all threads (timeout 5s)
  ↓
Print final statistics
  ↓
Exit(0)
```

---

## Integration Points

### Upstreams (Data Sources)

```
DATA SOURCES LAYER
├── Mobile Simulator → Kafka → topic_app_events
├── Web Simulator → Kafka → topic_app_events
├── CDC Simulator → Kafka → topic_cdc_changes
├── Clickstream Simulator → Kafka → topic_clickstream
└── External Data Simulator → Kafka → topic_external_data
```

### Downstreams (Used By)

```
PROCESSING LAYER (future)
├── Spark Streaming ← INGESTION LAYER metrics
├── Airflow DAGs ← INGESTION LAYER validated data
└── Feature Store ← INGESTION LAYER processed data
```

---

**Architecture Version:** 1.0  
**Last Updated:** February 16, 2026  
**Status:** ✅ Production Ready
