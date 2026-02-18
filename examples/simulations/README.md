# DATA SOURCES LAYER - Complete Simulation

## 📋 Overview

This comprehensive simulation implements all components of the **DATA SOURCES LAYER** in a production-grade data platform architecture.

### Data Sources Implemented

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES LAYER                            │
└─────────────────────────────────────────────────────────────────┘

1. APPLICATION DATA (Mobile/Web Apps)
   ├── 📱 Mobile App Simulator → FastAPI Gateway → Topic: topic_app_events
   ├── 🌐 Web App Simulator → FastAPI Gateway → Topic: topic_app_events
   └── 📚 Booking System Events → FastAPI Gateway → Topic: topic_app_events

2. OLTP CDC (Change Data Capture)
   ├── 📀 PostgreSQL Database (CDC enabled)
   ├── 🔄 CDC Simulator (simulates Debezium)
   └── 📤 Topic: topic_cdc_changes

3. STREAMING DATA
   ├── 🖱️  Clickstream Events → Topic: topic_clickstream
   ├── 📝 Application Logs → Topic: topic_app_logs
   └── 🚀 Real-time Streams → Spark Streaming Processing

4. EXTERNAL DATA (Batch)
   ├── 🌦️  Weather API → Topic: topic_external_data
   ├── 🗺️  Maps API → Topic: topic_external_data
   ├── 📰 News/Social Media → Topic: topic_external_data
   ├── 📊 Market Data → Topic: topic_external_data
   └── ✈️ Travel Trends → Topic: topic_external_data

5. INFRASTRUCTURE
   ├── 🎯 Apache Kafka (Event streaming platform)
   ├── 📋 Schema Registry (Avro schemas)
   ├── 🔍 Kafka UI (Monitoring & management)
   ├── ⚡ Spark Streaming (Real-time processing)
   ├── 🔄 Apache Airflow (Batch orchestration)
   └── 🐘 PostgreSQL (OLTP database + CDC)
```

---

## 🔧 Architecture Components

### 1. Application Data Layer
**Files:** `apps/api/main.py`, `apps/mobile/simulator.py`, `apps/web/simulator.py`

#### FastAPI Gateway (`apps/api/main.py`)
- **Endpoints:**
  - `POST /events/user` - Track user events from mobile/web
  - `POST /events/booking` - Track booking system events
  - `POST /events/batch` - Batch publish multiple events
  - `GET /health` - Health check
  - `GET /stats` - Event statistics

- **Features:**
  - Async event processing with FastAPI
  - Kafka producer integration
  - Structured event validation with Pydantic
  - Background task processing
  - Comprehensive logging

- **Event Types:**
  ```json
  {
    "event_id": "uuid",
    "event_type": "page_view|click|search|booking_view|click_cta",
    "user_id": "user_123",
    "session_id": "sess_abc",
    "app_type": "mobile|web",
    "timestamp": "2026-02-16T10:30:00Z",
    "properties": { "key": "value" }
  }
  ```

#### Mobile App Simulator (`apps/mobile/simulator.py`)
- Generates realistic user journeys:
  - App open → Home page → Search → Filter → Booking view → CTA click
  - 3-7 concurrent user simulations
  - Random delays between events
  - 70% conversion rate
  - Supports iOS device simulation

#### Web App Simulator (`apps/web/simulator.py`)
- Simulates desktop/browser user sessions:
  - Page navigation flows
  - Search and filtering
  - Shopping cart interactions
  - Checkout process
  - Device type tracking (desktop, tablet, mobile)

---

### 2. OLTP CDC (Change Data Capture)
**Files:** `postgres_cdc/simulator.py`, `postgres_cdc/init.sql`

#### PostgreSQL Configuration
- **Tables:**
  - `public.users` - User account data
  - `public.bookings` - Booking records
  - `public.payments` - Payment transactions

- **CDC Features:**
  - Logical replication enabled (`wal_level=logical`)
  - Replication slots for consistency
  - Publication on all relevant tables
  - Automatic updated_at timestamps

#### CDC Event Generation
```json
{
  "change_id": "uuid",
  "table_name": "public.bookings",
  "operation": "INSERT|UPDATE|DELETE",
  "primary_key": { "id": "uuid" },
  "before_values": { "status": "pending" },
  "after_values": { "status": "confirmed" },
  "timestamp": "2026-02-16T10:30:00Z",
  "source_database": "PostgreSQL"
}
```

#### Simulated Operations
- **INSERT:** New users, bookings, payments
- **UPDATE:** Booking status changes, payment reconciliation
- **DELETE:** Record deletion (rare)

---

### 3. Streaming Data Layer
**Files:** `spark_streaming/streaming_jobs.py`, `clickstream/simulator.py`

#### Clickstream Events
**Configuration:**
- **Rate:** 60 events per minute (configurable)
- **Duration:** Continuous stream
- **Topics:** `topic_clickstream`

**Event Schema:**
```json
{
  "click_id": "uuid",
  "user_id": "user_123",
  "session_id": "sess_abc",
  "page_url": "https://travel-booking.com/booking_detail",
  "element_id": "add_to_cart_button",
  "x_coordinate": 1024,
  "y_coordinate": 768,
  "timestamp": "2026-02-16T10:30:00Z",
  "device_type": "desktop|mobile|tablet"
}
```

#### Application Logs
- Generated from all services
- **Levels:** DEBUG, INFO, WARN, ERROR, FATAL
- **Topics:** `topic_app_logs`

#### Real-time Processing with Spark Streaming
**Jobs:**
1. **App Events Processing:**
   - Window-based aggregations (5-minute windows)
   - Event count by type and app
   - Unique user counting
   - Output to `topic_processed_events`

2. **Clickstream Analysis:**
   - 10-minute window aggregations
   - Click counts per page
   - Heat map data generation
   - User engagement metrics

3. **CDC Change Processing:**
   - Track database operations per table
   - Monitor data consistency
   - Flag suspicious patterns

---

### 4. External Data Layer
**Files:** `external_data/simulator.py`, `airflow/dags/*.py`

#### Data Sources
1. **Weather API** (`weather_data_ingestion.py`)
   - **Schedule:** Every 6 hours
   - **Data:** Temperature, humidity, wind speed, conditions
   - **Cities:** Ha Noi, Ho Chi Minh, Da Nang, Can Tho, Hai Phong

2. **Maps API** (`maps_data_ingestion.py`)
   - **Schedule:** Daily at midnight
   - **Data:** Coordinates, nearby hotels, ratings, popularity

3. **Configuration-Driven Pipeline** (`config_driven_pipeline.py`)
   - **Sources:**
     - Social Media (Twitter, Instagram, TikTok, Facebook)
     - Market Data (Stock prices, volumes)
     - News Feeds (RSS)
   - **Schedule:** Hourly
   - **Features:** Dynamic source configuration via dictionary

4. **External Data Simulator** (`external_data/simulator.py`)
   - Real-time simulation of all external sources
   - Random data generation for realistic patterns
   - Batch size: 50-100 events
   - Runs continuously

#### Airflow DAGs
- **Framework:** Apache Airflow 2.7.3
- **Executor:** LocalExecutor
- **Database:** PostgreSQL
- **DAG Pattern:** Task dependencies explicit

**DAG Structure:**
```
Fetch Data → Transform/Enrich → Validate → Publish to Kafka
```

---

## 🚀 Kafka Topics Configuration

| Topic | Partitions | Replication | Retention | Cleanup |
|-------|-----------|------------|-----------|---------|
| `topic_app_events` | 6 | 3 | 1 day | delete |
| `topic_cdc_changes` | 4 | 3 | 7 days | delete |
| `topic_clickstream` | 8 | 3 | 3 days | delete |
| `topic_app_logs` | 4 | 2 | 2 days | delete |
| `topic_external_data` | 3 | 2 | 30 days | delete |
| `topic_processed_events` | 6 | 3 | 7 days | delete |
| `topic_user_state` | 6 | 3 | ∞ | compact |
| `topic_booking_state` | 6 | 3 | ∞ | compact |

---

## 📊 Schema Registry (Avro Schemas)

All events are serialized using Avro for:
- Schema evolution
- Data validation
- Compact binary format
- Multi-language support

**Schemas Available:**
1. `AppEvent.avsc` - Application events
2. `CDCChange.avsc` - Database changes
3. `Clickstream.avsc` - Clickstream events
4. `AppLog.avsc` - Application logs

---

## 🐳 Docker Services

### Infrastructure Services
```yaml
Services Running:
├── Zookeeper (2181) - Kafka coordination
├── Kafka (9092) - Event broker
├── Schema Registry (8081) - Schema management
├── Kafka UI (8080) - Web monitoring
├── PostgreSQL (5432) - OLTP database
├── PostgreSQL Airflow (5433) - Workflow DB
├── Spark Master (7077, 8181) - Job coordination
├── Spark Worker - Computation nodes
├── Airflow Web (8888) - DAG UI
├── Airflow Scheduler - Task scheduling
├── FastAPI Gateway (8000) - API endpoint
├── Mobile Simulator - Event generation
├── Web Simulator - Event generation
├── CDC Simulator - Change capture
├── Clickstream Simulator - Click events
├── External Data Simulator - External sources
└── Streaming Jobs - Real-time processing
```

---

## 📈 Data Flow Diagrams

### Flow 1: Application Events
```
Mobile App → FastAPI /events/user → Kafka (topic_app_events)
Web App    → FastAPI /events/user → Kafka (topic_app_events)
Booking    → FastAPI /events/booking → Kafka (topic_app_events)
                                      ↓
                             Spark Streaming
                                      ↓
                    topic_processed_events (output)
```

### Flow 2: CDC Events
```
PostgreSQL (Insert/Update/Delete)
                ↓
        CDC Simulator (captures logs)
                ↓
        Kafka (topic_cdc_changes)
                ↓
        Spark Streaming (analyze)
                ↓
        topic_cdc_state (compacted topic)
```

### Flow 3: External Data
```
Airflow DAGs (scheduled tasks)
        ├── Fetch (Weather, Maps APIs)
        ├── Transform (enrich, validate)
        └── Publish to Kafka
                ↓
        topic_external_data
                ↓
        Downstream processors
```

---

## 🔧 Quick Start Guide

### Prerequisites
- Docker and Docker Compose
- 8+ GB RAM
- 20+ GB disk space

### 1. Start All Services
```bash
cd simulations/
docker-compose -f docker-compose-production.yml up -d
```

### 2. Verify Services
```bash
# Check Kafka
docker exec kafka kafka-topics --bootstrap-server kafka:9092 --list

# Check Airflow
open http://localhost:8888
# Username: airflow, Password: airflow

# Check Kafka UI
open http://localhost:8080

# Check FastAPI
open http://localhost:8000/docs
```

### 3. Monitor Data Flow
```bash
# Watch app events
docker exec kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic topic_app_events \
  --from-beginning

# Watch CDC events
docker exec kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic topic_cdc_changes \
  --from-beginning

# Watch clickstream
docker exec kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic topic_clickstream \
  --from-beginning
```

### 4. View Logs
```bash
# API Gateway
docker logs api-gateway -f

# Mobile Simulator
docker logs mobile-simulator -f

# CDC Simulator
docker logs cdc-simulator -f

# Spark Streaming
docker logs streaming-jobs -f
```

---

## 📊 Monitoring & Observability

### Kafka UI (`http://localhost:8080`)
- Topic management and monitoring
- Consumer group tracking
- Message inspection
- Schema Registry integration

### Airflow Web UI (`http://localhost:8888`)
- DAG execution monitoring
- Task logs and errors
- Schedule and trigger management
- XCom (inter-task communication) inspection

### Spark UI (`http://localhost:8181`)
- Job and task execution
- Resource utilization
- Stage analysis
- Executor logs

### FastAPI Swagger UI (`http://localhost:8000/docs`)
- Interactive API testing
- Request/response examples
- Schema documentation

---

## 🔄 Event Distribution (per minute)

Based on current simulation configuration:

| Source | Events/min | Total/hour | Configuration |
|--------|-----------|-----------|-----------------|
| Mobile App | 50-100 | 3,000-6,000 | 3-7 concurrent journeys |
| Web App | 30-60 | 1,800-3,600 | 2-5 concurrent sessions |
| Clickstream | 60 | 3,600 | Continuous stream |
| CDC (approximate) | 20-30 | 1,200-1,800 | Random operations |
| External Data | 20-40 | 1,200-2,400 | Batch intervals |
| **TOTAL** | **280-350** | **~18,000-22,000** | **Production-like** |

---

## 🛠️ Customization

### Adjust Event Volume
**File:** `simulators.py`
```python
# Mobile app events
simulate_continuous_traffic(duration_minutes=5)  # Change duration

# Clickstream rate
simulate_continuous_clickstream(events_per_minute=100)  # Change rate
```

### Change Airflow Schedule
**File:** `airflow/dags/*.py`
```python
dag = DAG(
    'weather_data',
    schedule_interval='0 */6 * * *',  # Change frequency
    ...
)
```

### Modify Kafka Topics
**File:** `kafka/config.py`
```python
TOPIC_CONFIGS = {
    "topic_app_events": {
        "partitions": 12,  # Increase partitions
        "replication_factor": 3,
        ...
    }
}
```

---

## 📚 Knowledge Base

### Key Concepts
- **Kafka:** Distributed event streaming platform
- **CDC (Change Data Capture):** Real-time database changes
- **Spark Streaming:** Real-time data processing
- **Airflow:** Workflow orchestration
- **Schema Registry:** Centralized schema management
- **Avro:** Serialization format with schema evolution

### Technologies
- **Kafka 7.5.0** - Event broker
- **Spark 3.5.0** - Stream processing
- **Airflow 2.7.3** - Workflow orchestration
- **PostgreSQL 15** - Database
- **Python 3.11** - Application code
- **FastAPI** - Web framework

---

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs kafka
docker-compose logs api

# Restart services
docker-compose down
docker-compose up -d --force-recreate
```

### Kafka Topics Not Created
```bash
# Manual creation
docker exec kafka kafka-topics \
  --create \
  --topic topic_app_events \
  --partitions 6 \
  --replication-factor 1 \
  --bootstrap-server kafka:9092
```

### Airflow DAGs Not Visible
```bash
# Refresh DAGs
docker exec airflow-webserver airflow dags list
docker exec airflow-scheduler airflow dags reparse
```

### Low Event Volume
- Check simulator logs: `docker logs mobile-simulator`
- Verify API health: `curl http://localhost:8000/health`
- Monitor Kafka: `docker logs kafka`

---

## 📝 Further Reading

### Documentation
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Schema Registry Guide](https://docs.confluent.io/schema-registry/latest/)
- [Spark Structured Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)

### Related Files
- Architecture diagram: See `diagrams/` directory
- Configuration details: `kafka/config.py`
- API specifications: `apps/api/main.py` (OpenAPI docs)
- Database schema: `postgres_cdc/init.sql`

---

## 📄 Summary

This implementation provides:

✅ **Complete Data Sources Layer** with all 4 primary sources
✅ **Production-grade Infrastructure** with proper scaling
✅ **Real-time & Batch Processing** capabilities
✅ **Schema Management** with Avro and Registry
✅ **Monitoring & Observability** at every level
✅ **Extensible Architecture** for easy customization
✅ **Comprehensive Documentation** and examples

**Ready for:** Testing, learning, simulation, and as a foundation for production pipelines!

---

*Last Updated: February 16, 2026*
*Version: 1.0.0 - Production Ready*
