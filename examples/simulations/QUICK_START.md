# Quick Start & Configuration Guide

## 🚀 Start in 3 Steps

### Step 1: Navigate to Simulations Directory
```bash
cd simulations/
```

### Step 2: Start All Services
```bash
docker-compose -f docker-compose-production.yml up -d
```

### Step 3: Verify Everything is Running
```bash
# Check all containers
docker-compose ps

# Expected output:
# NAME                      STATUS
# zookeeper                 Up
# kafka                     Up (healthy)
# schema-registry          Up (healthy)
# kafka-ui                 Up
# api-gateway              Up
# mobile-simulator         Up
# web-simulator            Up
# postgres                 Up
# cdc-simulator            Up
# spark-master             Up
# spark-worker             Up
# streaming-jobs          Up
# airflow-postgres        Up
# airflow-webserver       Up
# airflow-scheduler       Up
# clickstream-simulator   Up
# external-data-simulator Up
```

---

## 📊 Monitor Data in Real-Time

### Option 1: Kafka UI (Recommended)
Open browser → `http://localhost:8080`
- Visual topic browser
- Consumer group monitoring
- Live message inspection
- Schema Registry integration

### Option 2: Command Line
```bash
# Watch app events (application data layer)
docker exec kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic topic_app_events \
  --from-beginning \
  --max-messages 20

# Watch CDC events (database changes)
docker exec kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic topic_cdc_changes \
  --from-beginning \
  --max-messages 20

# Watch clickstream (user interactions)
docker exec kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic topic_clickstream \
  --from-beginning \
  --max-messages 20

# Watch external data (batch sources)
docker exec kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic topic_external_data \
  --from-beginning \
  --max-messages 20
```

---

## 🔌 API Endpoints

### FastAPI Gateway Documentation
Open browser → `http://localhost:8000/docs`

### Quick API Tests

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Send User Event (Mobile App):**
```bash
curl -X POST http://localhost:8000/events/user \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "page_view",
    "user_id": "user_123",
    "session_id": "sess_abc",
    "app_type": "mobile",
    "timestamp": "2026-02-16T10:30:00Z",
    "properties": {
      "page": "booking_detail",
      "destination": "Ha Noi"
    }
  }'
```

**Send Booking Event:**
```bash
curl -X POST http://localhost:8000/events/booking \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "booking_created",
    "booking_id": "book_123",
    "user_id": "user_123",
    "properties": {
      "destination": "Da Nang",
      "price": 250.00
    }
  }'
```

**Batch Publish Events:**
```bash
curl -X POST http://localhost:8000/events/batch \
  -H "Content-Type: application/json" \
  -d '[
    {
      "event_type": "click",
      "source_app": "mobile_app",
      "data": {"button": "book_now"}
    },
    {
      "event_type": "search",
      "source_app": "web_app",
      "data": {"destination": "Ho Chi Minh"}
    }
  ]'
```

---

## 📋 Airflow Workflows

### Access Airflow Web UI
Open browser → `http://localhost:8888`
- **Username:** `airflow`
- **Password:** `airflow`

### Available DAGs

#### 1. Weather Data Ingestion
- **Schedule:** Every 6 hours (0 */6 * * *)
- **Tasks:**
  1. `fetch_weather_data` - Call weather API
  2. `transform_weather_data` - Format and enrich
  3. `publish_to_kafka` - Publish to topic_external_data
- **Output:** Weather data with temperature, humidity, wind
- **Cities:** Ha Noi, Ho Chi Minh, Da Nang, Can Tho, Hai Phong

#### 2. Maps Data Ingestion
- **Schedule:** Daily at midnight (0 0 * * *)
- **Tasks:**
  1. `fetch_maps_data` - Get location data
  2. `enrich_with_metadata` - Add analytics metrics
  3. `publish_to_kafka` - Publish enriched data
- **Output:** Maps data with coordinates, hotels, ratings

#### 3. Configuration-Driven Pipeline
- **Schedule:** Hourly (@hourly)
- **Tasks:**
  - `fetch_*` - Parallel fetch from all sources
  - `process_and_validate` - Data quality checks
  - `publish_to_kafka` - Publish validated data
- **Sources:**
  - Social Media (Twitter, Instagram, TikTok)
  - Market Data (Stocks)
  - News (RSS feeds)
- **Enable/Disable:** Modify source config in DAG

---

## 📊 Spark Streaming Analysis

### Access Spark UI
Open browser → `http://localhost:8181`

### Running Streaming Jobs
```bash
# Check logs
docker logs streaming-jobs -f

# Spark is processing:
# 1. Application events (5-minute windows)
# 2. Clickstream data (10-minute windows)
# 3. CDC changes (operational metrics)
```

### View Output
```bash
# Processed events
docker exec kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic topic_processed_events \
  --max-messages 10
```

---

## 🗂️ Directory Structure

```
simulations/
├── README.md                           # Main documentation
├── QUICK_START.md                      # This file
├── docker-compose-production.yml       # All services configuration
│
├── apps/
│   ├── api/                            # FastAPI Application Layer
│   │   ├── main.py                     # Gateway implementation
│   │   ├── Dockerfile                  # Container image
│   │   └── requirements.txt            # Dependencies
│   ├── mobile/                         # Mobile App Simulator
│   │   ├── simulator.py                # Event generator
│   │   └── Dockerfile
│   └── web/                            # Web App Simulator
│       ├── simulator.py                # Event generator
│       └── Dockerfile
│
├── kafka/
│   └── config.py                       # Topic configurations & schemas
│
├── schema_registry/
│   ├── AppEvent.avsc                   # App event schema
│   ├── CDCChange.avsc                  # CDC event schema
│   ├── Clickstream.avsc                # Clickstream schema
│   └── AppLog.avsc                     # Log schema
│
├── postgres_cdc/
│   ├── simulator.py                    # CDC event generator
│   ├── init.sql                        # Database initialization
│   ├── Dockerfile
│   └── requirements.txt
│
├── spark_streaming/
│   ├── streaming_jobs.py               # Real-time processing
│   └── requirements.txt
│
├── airflow/
│   ├── dags/                           # Scheduled pipelines
│   │   ├── weather_data_ingestion.py   # Weather API
│   │   ├── maps_data_ingestion.py      # Maps API
│   │   └── config_driven_pipeline.py   # Multi-source
│   ├── .env                            # Airflow config
│   ├── logs/                           # Task logs
│   └── plugins/                        # Custom operators
│
├── clickstream/
│   └── simulator.py                    # Click event generator
│
└── external_data/
    └── simulator.py                    # Multi-source simulator
```

---

## 🔍 Monitoring Checklist

### Health Checks
```bash
# All containers running?
docker-compose ps | grep -c "Up"  # Should be 16

# Kafka healthy?
docker exec kafka kafka-broker-api-versions \
  --bootstrap-server kafka:9092

# Topics created?
docker exec kafka kafka-topics \
  --list --bootstrap-server kafka:9092

# API responding?
curl -s http://localhost:8000/health | jq

# Airflow ready?
curl -s http://localhost:8888 | head -20
```

### Data Flow Verification
1. **Application Events:**
   - ✅ Mobile simulator running: `docker logs mobile-simulator`
   - ✅ Web simulator running: `docker logs web-simulator`
   - ✅ Events in topic: Check Kafka UI / topic_app_events

2. **CDC Changes:**
   - ✅ PostgreSQL running: `docker exec postgres pg_isready`
   - ✅ CDC simulator running: `docker logs cdc-simulator`
   - ✅ Events in topic: Check Kafka UI / topic_cdc_changes

3. **Clickstream:**
   - ✅ Simulator running: `docker logs clickstream-simulator`
   - ✅ Events in topic: Check Kafka UI / topic_clickstream

4. **External Data:**
   - ✅ Airflow DAGs running: Check Airflow UI
   - ✅ Simulator running: `docker logs external-data-simulator`
   - ✅ Events in topic: Check Kafka UI / topic_external_data

5. **Streaming Processing:**
   - ✅ Spark jobs active: Check Spark UI
   - ✅ Output topics populated: Check Kafka UI / topic_processed_events

---

## ⚙️ Configuration Options

### Adjust Data Volume

**Mobile App Events (apps/mobile/simulator.py):**
```python
simulate_continuous_traffic(duration_minutes=30)  # Default: 30 minutes
```

**Web App Events (apps/web/simulator.py):**
```python
simulate_continuous_traffic(duration_minutes=30)  # Default: 30 minutes
```

**Clickstream Rate (clickstream/simulator.py):**
```python
events_per_minute=60  # Increase for higher volume
```

**CDC Update Frequency (postgres_cdc/simulator.py):**
- Modify `time.sleep(random.uniform(2, 5))` for frequency

**External Data Batch Size (external_data/simulator.py):**
```python
events_per_batch=50  # Adjust batch size
```

### Change Kafka Topic Partitions
Edit `docker-compose-production.yml`:
```yaml
kafka:
  environment:
    KAFKA_NUM_PARTITIONS: 12  # Default: 6
    KAFKA_DEFAULT_REPLICATION_FACTOR: 3
```

### Modify Airflow Schedule
Edit `airflow/dags/*.py`:
```python
dag = DAG(
    'weather_data',
    schedule_interval='@hourly',  # Change: '@daily', '0 */6 * * *', etc
)
```

---

## 🚨 Troubleshooting

### Issue: "Topic does not exist"
```bash
# Create missing topic
docker exec kafka kafka-topics --create \
  --topic topic_app_events \
  --partitions 6 \
  --replication-factor 1 \
  --bootstrap-server kafka:9092
```

### Issue: "Connection refused"
```bash
# Wait for services to be ready
docker-compose ps

# If not healthy, restart
docker-compose restart kafka
```

### Issue: "API not accepting events"
```bash
# Check if API is running
docker logs api-gateway

# Verify health endpoint
curl http://localhost:8000/health

# Restart API
docker-compose restart api
```

### Issue: "Airflow DAGs not running"
```bash
# Check scheduler logs
docker logs airflow-scheduler -f

# Trigger DAG manually
docker exec airflow-webserver airflow dags test \
  weather_data_ingestion 2026-02-16
```

### Issue: "No events in Kafka"
```bash
# Check simulators
docker logs mobile-simulator | tail -20
docker logs cdc-simulator | tail -20
docker logs clickstream-simulator | tail -20

# Restart all simulators
docker-compose restart mobile-simulator web-simulator \
  cdc-simulator clickstream-simulator external-data-simulator
```

---

## 📈 Performance Tuning

### Increase Throughput
1. **Kafka:**
   - Increase partitions: `KAFKA_NUM_PARTITIONS: 12`
   - Tune batch size in producers

2. **Spark:**
   - Scale workers: Add more `spark-worker` services
   - Increase executor memory: Edit docker-compose

3. **Simulators:**
   - Reduce event delays
   - Increase concurrent users/sessions

### Reduce Latency
1. **Kafka batching:**
   ```python
   linger_ms=1,      # Reduce wait time
   batch_size=4096   # Smaller batches
   ```

2. **Spark windows:**
   - Reduce window duration: `window("1 minute")` instead of "5 minutes"

3. **Airflow:**
   - Run DAGs more frequently
   - Reduce task dependencies

---

## 📚 Next Steps

1. **Explore Data:**
   - Browse topics in Kafka UI
   - Check event schemas in Schema Registry
   - Inspect messages in detail

2. **Custom Processing:**
   - Add new DAGs in `airflow/dags/`
   - Create custom Spark jobs in `spark_streaming/`
   - Extend API with new endpoints

3. **Scale Up:**
   - Multiple Spark workers
   - More Kafka brokers
   - Distributed Airflow installation

4. **Production:**
   - Add authentication (Kafka, Airflow, APIs)
   - Configure persistent storage
   - Set up monitoring/alerting
   - Implement backup strategies

---

## 📞 Support

For detailed documentation, see: `README.md`
For API examples, visit: `http://localhost:8000/docs`
For architecture details, check: `docker-compose-production.yml`

---

Happy Data Platforming! 🚀

*Last Updated: February 16, 2026*
