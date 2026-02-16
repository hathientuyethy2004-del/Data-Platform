# Data Platform - Architecture & Data Flow Documentation

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES LAYER - COMPLETE SYSTEM                    │
└──────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────┐
                              │   DATA SOURCES      │
                              └─────────────────────┘
                                      │
                  ┌─────────────────────┼─────────────────────┐
                  │                     │                     │
        ┌─────────▼──────────┐ ┌──────▼────────┐ ┌──────────▼────────┐
        │  APPLICATION DATA  │ │   CDC (OLTP)  │ │  STREAMING DATA   │
        ├────────────────────┤ ├───────────────┤ ├───────────────────┤
        │ • Mobile App       │ │ • PostgreSQL  │ │ • Clickstream     │
        │ • Web App          │ │ • MySQL       │ │ • Application     │
        │ • Booking System   │ │ • MongoDB     │ │   Logs            │
        │                    │ │ • CDC Events  │ │ • IoT Data        │
        └──────────┬─────────┘ └───────┬───────┘ └─────────┬─────────┘
                   │                   │                   │
                   └───────────────────┼───────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │   EXTERNAL DATA (Batch)            │
                    ├───────────────────────────────────┤
                    │ • Weather API → Airflow DAG       │
                    │ • Maps API → Airflow DAG          │
                    │ • News/Social Media → Config DAG  │
                    │ • Market Data → Config DAG        │
                    └──────────────────┬────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │   KAFKA INGESTION LAYER            │
                    │  (Event Streaming Platform)        │
                    ├───────────────────────────────────┤
                    │ • Zookeeper (coordination)         │
                    │ • Kafka Brokers (3-node cluster)   │
                    │ • Schema Registry (Avro schemas)   │
                    │ • Kafka UI (monitoring)            │
                    └──────────────────┬────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │         KAFKA TOPICS (Events) │                             │
        │                               │                             │
        ├─────────────────┬─────────────┴───────┬────────────┬───────┤
        │                 │                     │            │       │
   ┌────▼──────┐  ┌──────▼───────┐  ┌────────▼──┐  ┌──────▼──┐  ┌──▼─────┐
   │topic_app_ │  │topic_cdc_    │  │topic_     │  │topic_app│  │topic_  │
   │events     │  │changes       │  │clickstream│  │_logs    │  │external│
   │           │  │              │  │           │  │         │  │_data   │
   └────┬──────┘  └──────┬───────┘  └────┬──────┘  └─────┬───┘  └──┬─────┘
        │                │                │              │         │
        └────────────────┼────────────────┼──────────────┼─────────┘
                         │
                    ┌────▼───────────────────────────────┐
                    │   STREAM PROCESSING & ANALYTICS   │
                    ├───────────────────────────────────┤
                    │ • Spark Structured Streaming      │
                    │ • Real-time aggregations          │
                    │ • Window functions (5-10 min)     │
                    │ • Event enrichment & validation   │
                    └────┬───────────────────────────────┘
                         │
                    ┌────▼───────────────────────────────┐
                    │   DATA WAREHOUSE / PROCESSING     │
                    ├───────────────────────────────────┤
                    │ • topic_processed_events          │
                    │ • topic_user_state (compacted)    │
                    │ • topic_booking_state (compacted) │
                    │ • Analytics databases             │
                    └───────────────────────────────────┘
```

---

## Data Flow Details

### 1. Application Data Flow

#### Architecture:
```
┌───────────────────────────────┐
│   Application Layer           │
├───────────────────────────────┤
│ Mobile App | Web App | Booking│
└───────────────┬───────────────┘
                │ HTTP/REST
                ▼
        ┌──────────────────┐
        │  FastAPI Gateway │
        │  (apps/api/)     │
        ├──────────────────┤
        │ /events/user     │
        │ /events/booking  │
        │ /events/batch    │
        │ /health          │
        └──────────┬───────┘
                   │ Async Publishing
                   │ (Background Tasks)
                   ▼
        ┌──────────────────────────┐
        │  Kafka Producer          │
        ├──────────────────────────┤
        │ Config: acks=all         │
        │ Compression: snappy      │
        │ Retries: 3               │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  Kafka Topic             │
        │  topic_app_events        │
        ├──────────────────────────┤
        │ Partitions: 6            │
        │ Replication: 3           │
        │ Retention: 1 day         │
        └──────────────────────────┘
```

#### Event Schema:
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "page_view",
  "user_id": "user_123",
  "session_id": "sess_abc",
  "app_type": "mobile",
  "timestamp": "2026-02-16T10:30:45.123Z",
  "properties": {
    "page": "booking_detail",
    "destination": "Ha Noi",
    "price": "250.00"
  }
}
```

#### Event Types:
- **Mobile/Web:** `page_view`, `click`, `search`, `filter_applied`, `booking_view`, `click_cta`
- **Booking:** `booking_created`, `booking_updated`, `payment_completed`, `booking_cancelled`
- **API:** Custom events via batch endpoint

#### Simulator Configuration:
- **Mobile:** 3-7 concurrent user journeys, 1-3 second delays
- **Web:** 2-5 concurrent sessions, 2-5 second page load times
- **Generated Events/Hour:** 4,000-10,000

---

### 2. CDC (Change Data Capture) Flow

#### Architecture:
```
┌──────────────────────┐
│   PostgreSQL DB      │
│  (travel_booking)    │
├──────────────────────┤
│ Tables:              │
│ • users              │
│ • bookings           │
│ • payments           │
│ • WAL logs           │
└──────────┬───────────┘
           │ Logical Replication
           │ (wal_level=logical)
           ▼
    ┌─────────────────────┐
    │  CDC Simulator      │
    │  (Debezium-like)    │
    ├─────────────────────┤
    │ Captures:           │
    │ • INSERT events     │
    │ • UPDATE events     │
    │ • DELETE events     │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  Kafka Producer     │
    │  (topic_cdc_change)│
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │ topic_cdc_changes   │
    ├─────────────────────┤
    │ Partitions: 4       │
    │ Replication: 3      │
    │ Retention: 7 days   │
    └─────────────────────┘
```

#### CDC Event Schema:
```json
{
  "change_id": "550e8400-e29b-41d4-a716-446655440000",
  "table_name": "public.bookings",
  "operation": "UPDATE",
  "primary_key": {
    "id": "book_123"
  },
  "before_values": {
    "status": "pending"
  },
  "after_values": {
    "status": "confirmed"
  },
  "timestamp": "2026-02-16T10:30:45.123Z",
  "source_database": "PostgreSQL",
  "debezium_metadata": {
    "source": {
      "connector": "postgresql",
      "db": "travel_booking",
      "schema": "public"
    },
    "transaction_ts": 1708077045123
  }
}
```

#### Operations Simulated:
- **INSERT:** New users: 5-10/min, Bookings: 2-5/min, Payments: 1-3/min
- **UPDATE:** Status changes, payment reconciliation
- **DELETE:** Rare operations

#### Database Configuration:
- **Replication:** Logical (wal_level=logical)
- **Slots:** 10 replication slots
- **Publication:** cdc_publication on all tracked tables
- **Retention:** 7 days of WAL logs

---

### 3. Streaming Data Flow

#### Architecture:
```
┌──────────────────────────────┐
│   Real-time Data Sources     │
├──────────────────────────────┤
│ • User Clickstream           │
│ • Application Logs           │
│ • System Events              │
│ • IoT Streams (simulated)    │
└──────────┬───────────────────┘
           │
    ┌──────▼──────────┐
    │   Kafka Topics  │
    ├─────────────────┤
    │ topic_clickst   │
    │ topic_app_logs  │
    └──────┬──────────┘
           │
    ┌──────▼──────────────────────┐
    │  Spark Structured Streaming │
    ├──────────────────────────────┤
    │ • ReadStream from Kafka      │
    │ • Apply transformations      │
    │ • Window aggregations        │
    │ • Event enrichment           │
    └──────┬───────────────────────┘
           │
    ┌──────▼──────────────────┐
    │   Output Streams        │
    ├──────────────────────────┤
    │ topic_processed_events  │
    │ Console output          │
    │ Analytics DB            │
    └──────────────────────────┘
```

#### Clickstream Events/Minute:
- **Rate:** 60 events/minute (configurable)
- **Distribution:** 8 partitions across Kafka
- **Retention:** 3 days
- **Processing:** 10-minute windows

#### Event Schema:
```json
{
  "click_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_123",
  "session_id": "sess_abc",
  "page_url": "https://travel-booking.com/booking_detail",
  "element_id": "add_to_cart_button",
  "x_coordinate": 1024,
  "y_coordinate": 768,
  "timestamp": "2026-02-16T10:30:45.123Z",
  "device_type": "desktop"
}
```

#### Spark Streaming Jobs:

**1. Application Events Stream**
- Input: `topic_app_events`
- Window: 5 minutes
- Output: Event counts by type and app, unique users per window
- Output Topic: `topic_processed_events`

**2. Clickstream Analysis**
- Input: `topic_clickstream`
- Window: 10 minutes
- Output: Page click counts, user engagement metrics
- Enrichment: Add derived metrics (ctr, conversion)

**3. CDC Change Tracking**
- Input: `topic_cdc_changes`
- Window: 5 minutes
- Output: Operations per table, data consistency metrics

---

### 4. External Data Flow

#### Architecture:
```
┌─────────────────────────────┐
│   Airflow Orchestration     │
├─────────────────────────────┤
│ Apache Airflow 2.7.3        │
│ LocalExecutor               │
│ PostgreSQL Metadata DB      │
└──────────┬──────────────────┘
           │
     ┌─────┴──────┬──────────┬──────────┐
     │            │          │          │
┌────▼──┐  ┌─────▼──┐  ┌───▼──┐  ┌────▼────┐
│Weather│  │ Maps   │  │Config │  │External │
│DAG    │  │DAG     │  │DAG    │  │Simulator│
└────┬──┘  └─────┬──┘  └───┬──┘  └────┬────┘
     │           │         │          │
     └───┬───────┴────┬────┴──────────┘
         │            │
    ┌────▼──────────┬─▼────────┐
    │ Fetch Data    │ Transform│
    │ (Weather API) │ (enrich) │
    ├───────────────┴──────────┤
    │ Validate                 │
    │ (data quality)           │
    ├──────────────────────────┤
    │ Publish to Kafka         │
    │ (topic_external_data)    │
    └──────────┬───────────────┘
               │
    ┌──────────▼──────────────┐
    │topic_external_data      │
    ├─────────────────────────┤
    │ Partitions: 3           │
    │ Replication: 2          │
    │ Retention: 30 days      │
    └─────────────────────────┘
```

#### DAG Details:

**1. Weather Data Ingestion**
```
Scheduled: 0 */6 * * * (every 6 hours)

Tasks:
  fetch_weather_data
    ├── Input: Cities list (external API)
    ├── Output: XCom['weather_data']
    └── Time: ~10 seconds

  transform_weather_data
    ├── Input: XCom['weather_data']
    ├── Actions: Enrich, standardize
    └── Output: XCom['transformed_data']

  publish_to_kafka
    ├── Input: XCom['transformed_data']
    ├── Topic: topic_external_data
    └── Records/Run: 5 (one per city)
```

**2. Maps Data Ingestion**
```
Scheduled: 0 0 * * * (daily at midnight)

Tasks:
  fetch_maps_data
    ├── Endpoints: Coordinates, hotels nearby
    ├── Cities: Ha Noi, Ho Chi Minh, etc.
    └── Records: 5

  enrich_with_metadata
    ├── Add: Analytics, ratings
    ├── Add: Popularity scores
    └── Add: Timestamp

  publish_to_kafka
    ├── Topic: topic_external_data
    └── Format: JSON with nested objects
```

**3. Configuration-Driven Pipeline**
```
Scheduled: @hourly

Sources (configurable):
  1. Social Media API
     ├── Platforms: Twitter, Instagram, TikTok, Facebook
     ├── Metrics: Engagement, reach, sentiment
     └── Batch size: 100

  2. Market Data API
     ├── Symbols: AAPL, GOOGL, AMZN, MSFT, TSLA
     ├── Metrics: Price, volume, change
     └── Batch size: 50

  3. News Feed (RSS)
     ├── Feeds: Multiple sources
     ├── Parse: Article metadata
     └── Batch size: 50

Pipeline:
  Fetch (parallel) → Process → Validate → Publish
```

**4. External Data Simulator**
```
Generates: All types of external data continuously

Data Types:
  • Weather (cities, metrics)
  • Market Data (symbols, OHLCV)
  • Social Media (platforms, sentiment)
  • Travel Trends (category, region, metrics)

Rate: 50-100 events per batch, 5-15 second intervals
Output: topic_external_data
Continuous: Runs during entire simulation
```

#### Event Schema:
```json
{
  "external_data_id": "weather_ha_noi_1708077045123",
  "source": "weather_api",
  "source_type": "api",
  "timestamp": "2026-02-16T06:00:00.000Z",
  "data": {
    "city": "Ha Noi",
    "temperature": 24.5,
    "humidity": 75,
    "wind_speed": 8.2,
    "condition": "Clear",
    "pressure_mb": 1013.2
  }
}
```

---

## Kafka Topics Overview

| Topic | Partitions | Replication | Retention | Cleanup | Purpose |
|-------|-----------|------------|-----------|---------|---------|
| `topic_app_events` | 6 | 3 | 1 day | delete | Mobile/Web/Booking events |
| `topic_cdc_changes` | 4 | 3 | 7 days | delete | Database change events |
| `topic_clickstream` | 8 | 3 | 3 days | delete | User click events |
| `topic_app_logs` | 4 | 2 | 2 days | delete | Application logs |
| `topic_external_data` | 3 | 2 | 30 days | delete | External API data |
| `topic_processed_events` | 6 | 3 | 7 days | delete | Spark processed events |
| `topic_user_state` | 6 | 3 | ∞ | compact | User state store |
| `topic_booking_state` | 6 | 3 | ∞ | compact | Booking state store |

---

## Schema Registry & Avro Schemas

### Registered Schemas:
1. **AppEvent** - Application user events
2. **CDCChange** - Database change captures
3. **Clickstream** - Click events
4. **AppLog** - Application logs

All schemas stored in `schema_registry/` as `.avsc` files and registered in Confluent Schema Registry.

---

## Performance Metrics

### Throughput (per minute):
- **Mobile App:** 50-100 events
- **Web App:** 30-60 events
- **Clickstream:** 60 events
- **CDC:** 20-30 events
- **External Data:** 20-40 events
- **TOTAL:** 280-350 events/minute (~18K-21K/hour)

### Latency:
- **API to Kafka:** <100ms
- **Mobile Event Processing:** 200-500ms
- **Spark Window Output:** 5-10 minutes
- **Airflow Task Execution:** 10-30 seconds per task

### Resource Utilization:
- **Kafka:** 200-400MB heap
- **Schema Registry:** 128MB heap
- **Spark Master:** 1GB
- **Spark Workers:** 2GB each
- **Airflow:** 512MB + job overhead

---

## Data Quality & Monitoring

### Validation:
- Pydantic models for API input validation
- Avro schema validation in Kafka
- Spark DataFrame schema matching
- Airflow XCom data validation

### Error Handling:
- Kafka producer retries (3 attempts)
- Airflow task retries (2 attempts, 5min backoff)
- Exception logging in all components
- Dead-letter topics (future: could implement)

### Monitoring:
- Kafka UI dashboard (localhost:8080)
- Airflow Web UI (localhost:8888)
- Spark UI (localhost:8181)
- Docker container health checks
- Application logs in docker logs

---

## Extension Points

### Add Custom Data Source:
1. Create simulator in new directory
2. Configure Kafka producer
3. Add topic in docker-compose
4. Integrate with Spark streaming (if real-time)

### Add Custom Processing:
1. Create new Spark job or Airflow DAG
2. Input from existing topics
3. Output to new topic or external system
4. Monitor via Spark UI or Airflow UI

### Add Custom Sink:
1. Create consumer application
2. Subscribe to desired topic
3. Transform and load to target system
4. Implement failure handling and retries

---

This documentation provides the complete technical blueprint for understanding and extending the Data Platform's data sources layer!
