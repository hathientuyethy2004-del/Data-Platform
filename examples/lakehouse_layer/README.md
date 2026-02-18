# Lakehouse Layer

Complete lakehouse implementation using Delta Lake with Bronze/Silver/Gold architecture.

## 📋 Overview

The lakehouse layer provides:

- **Delta Lake**: ACID transactions, time travel, schema enforcement
- **Three-Layer Architecture**:
  - **Bronze**: Raw data from processing layer
  - **Silver**: Cleaned, deduplicated, enriched data
  - **Gold**: Business-ready aggregated tables
- **Data Catalog**: Metadata management and lineage tracking
- **Data Quality**: Automated quality checks and validation
- **REST API**: Query and metadata endpoints
- **Monitoring**: Health checks and performance metrics

## 📁 Structure

```
lakehouse_layer/
├── configs/
│   ├── lakehouse_config.py      # Configuration management
│   └── logging_config.py        # Logging setup
├── jobs/
│   ├── bronze/
│   │   └── app_events_ingestion.py  # Bronze ingestion job
│   ├── silver/
│   │   └── transformations.py       # Silver transformation job
│   └── gold/
│       └── aggregations.py          # Gold aggregation job
├── catalog/
│   └── data_catalog.py          # Metadata catalog
├── utils/
│   ├── delta_utils.py           # Delta Lake operations
│   ├── schemas.py               # Table schemas
│   └── quality_checks.py        # Data quality validation
├── api/
│   └── lakehouse_api.py         # REST API server
├── monitoring/
│   └── health_monitor.py        # Health check and monitoring
├── data/                        # Data storage (local development)
├── logs/                        # Application logs
└── docker-compose.yml           # Docker orchestration
```

## 🚀 Quick Start

### Local Development

```bash
cd /workspaces/Data-Platform/lakehouse_layer

# Install dependencies
pip install -r requirements.txt

# Run Bronze ingestion job
export PYTHONPATH=/workspaces/Data-Platform/lakehouse_layer:$PYTHONPATH
python jobs/bronze/app_events_ingestion.py

# Run Silver transformation job
python jobs/silver/transformations.py

# Run Gold aggregation job
python jobs/gold/aggregations.py

# Start API server
python api/lakehouse_api.py
```

### Docker Deployment

```bash
# Build and start lakehouse API
docker-compose -p lakehouse up -d lakehouse-api

# Check health
curl http://localhost:8888/health

# Access API
curl http://localhost:8888/tables
curl http://localhost:8888/query -X POST -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM gold_tables LIMIT 10"}'
```

## 📊 Data Architecture

### Bronze Layer (Raw Data)
- Ingests from processing layer outputs
- Minimal transformation
- Partitioned by timestamp
- High compression (snappy)
- Data quality flagging

**Tables**:
- `app_events_bronze` - Raw application events
- `clickstream_bronze` - Raw user clickstream data
- `cdc_changes_bronze` - Raw CDC change data

### Silver Layer (Cleaned Data)
- Deduplication and validation
- Schema enforcement
- Enrichment (session metrics, user dimensions)
- Removed bad records
- Optimized for queries

**Tables**:
- `app_events_silver` - Cleaned events
- `clickstream_silver` - Session-level clickstream
- `users_silver` - User dimension

### Gold Layer (Business-Ready)
- Aggregated metrics
- KPI calculations
- User segments
- Ready for BI/analytics tools

**Tables**:
- `event_metrics_gold` - Hourly event metrics
- `user_segments_gold` - User behavioral segments
- `daily_summary_gold` - Daily KPIs
- `hourly_metrics_gold` - Operational metrics

## 🔧 Configuration

### Environment Variables

```bash
SPARK_MASTER=spark://spark-master:7077
LAKEHOUSE_BASE_PATH=/var/lib/lakehouse
BRONZE_PATH=/var/lib/lakehouse/bronze
SILVER_PATH=/var/lib/lakehouse/silver
GOLD_PATH=/var/lib/lakehouse/gold
LOG_LEVEL=INFO
ENABLE_DELTA=true
AUTO_OPTIMIZE=true
TIME_TRAVEL_RETENTION_DAYS=30
VACUUM_RETENTION_DAYS=7
```

### Table Schemas

All table schemas are defined in `utils/schemas.py` with:
- Proper data types
- Nullable constraints
- Timestamp tracking
- Metadata fields

## 📡 REST API Endpoints

### Health & Status
```bash
GET /health
GET /catalog
```

### Table Operations
```bash
GET /tables                           # List all tables
GET /tables?layer=silver              # Filter by layer
GET /tables/{table_name}              # Get table metadata
GET /tables/{table_name}/preview      # Preview table data (limit 10)
```

### Query Execution
```bash
POST /query
{
  "sql": "SELECT * FROM gold_tables LIMIT 100",
  "limit": 1000
}
```

### Lineage & Catalog
```bash
GET /catalog/lineage/{table_name}     # Data lineage for table
```

## 🔍 Data Quality

Automatic quality checks for:
- ✅ Null value percentages
- ✅ Duplicate detection
- ✅ Data type validation
- ✅ Value range validation
- ✅ Schema completeness

## 📊 Monitoring

### Health Monitor

```bash
python monitoring/health_monitor.py
```

Generates comprehensive reports:
- Layer health status
- Table freshness
- Storage statistics
- Data quality metrics

## 🔗 Data Lineage

Automatic lineage tracking:
- Source → Target table mappings
- Transformation jobs
- Operation types (load, transform, aggregate)
- Timestamp tracking

## 💾 Data Retention

Configurable retention policies:
- Bronze: 30 days (raw data)
- Silver: 90 days (cleaned)
- Gold: 365 days (business data)
- Automatic vacuum and archive

## 🔐 Data Governance

- **Catalog**: Central metadata repository
- **Lineage**: Complete data provenance
- **Quality Checks**: Automated validation
- **Tags**: Table categorization
- **Ownership**: Track table owners

## 📈 Performance Optimization

- Z-order clustering for common queries
- Partitioning by date for efficient pruning
- Snappy compression for storage
- Delta Lake optimization
- Vacuum for transaction log cleanup

## 🐛 Troubleshooting

### No data in tables
1. Check processing layer outputs exist: `/workspaces/Data-Platform/processing_layer/outputs/`
2. Run Bronze ingestion job
3. Check logs: `/var/lib/lakehouse/logs/`

### Connection to Spark
1. Verify Spark cluster running: `docker ps | grep spark`
2. Check SPARK_MASTER setting
3. Ensure Docker network connectivity

### API not responding
1. Check health: `curl -v http://localhost:8888/health`
2. Check container logs: `docker logs lakehouse-api`
3. Verify volume mounts

## 📚 Resources

- [Delta Lake Documentation](https://docs.delta.io/)
- [Apache Spark SQL](https://spark.apache.org/docs/latest/sql-programming-guide.html)
- [FastAPI](https://fastapi.tiangolo.com/)

## 🤝 Contributing

Add new tables:
1. Define schema in `utils/schemas.py`
2. Create ingestion job
3. Register in catalog: `catalog.register_table()`
4. Add quality checks

## 📝 License

MIT License - See LICENSE file
