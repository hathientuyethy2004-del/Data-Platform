# 🚀 INGESTION LAYER - Quick Start

## 5 Phút Setup

### Bước 1: Verify DATA SOURCES LAYER

```bash
# Check if simulations are running
docker ps | grep -E "kafka|simulator"

# Should see:
# kafka             Up ... (healthy)
# mobile-simulator  Up ...
# web-simulator     Up ...
# cdc-simulator     Up ...
# clickstream-simulator  Up ...
# external-data-simulator Up ...
```

### Bước 2: Build INGESTION LAYER

```bash
cd /workspaces/Data-Platform/ingestion_layer

# Build Docker images
docker-compose build

# Should complete in 1-2 minutes
```

### Bước 3: Start INGESTION LAYER

```bash
# Start all consumers
docker-compose up -d

# Check if all started
docker-compose ps

# Should see 5 containers: healthy or starting
```

### Bước 4: View Logs

```bash
# Follow real-time logs
docker-compose logs -f

# Or specific consumer
docker-compose logs -f ingestion-unified

#After ~10 seconds should see metrics:
#📊 INGESTION LAYER METRICS:
#⚡ Throughput: 42.5 msgs/sec
#⏱️ Latency: 5.7ms avg
```

### Bước 5: Monitor

Access Kafka UI: http://localhost:8080
- View topics: topic_app_events, topic_cdc_changes, etc.
- See message counts increasing
- Check consumer groups: app_events_consumer, cdc_consumer, etc.

---

## 🔍 Monitoring Checklist

- [ ] All 5 containers running: `docker-compose ps`
- [ ] Kafka topics visible in KafkaUI: http://localhost:8080/topics
- [ ] Message count increasing
- [ ] Consumer lag low (<10000 messages)
- [ ] Error rate <1%
- [ ] Throughput >10 msgs/sec

---

## 🛑 Stop INGESTION LAYER

```bash
docker-compose down
```

---

## 📊 Key Metrics to Watch

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Throughput (msgs/sec) | >10 | 5-10 | <5 |
| Latency (avg ms) | <10 | 10-50 | >50 |
| Error Rate (%) | <1 | 1-5 | >5 |
| Consumer Lag | <1000 | 1000-10000 | >10000 |

---

## 🐛 Quick Troubleshooting

```bash
# Check Kafka connectivity
docker exec ingestion-unified python -c "from kafka import KafkaConsumer; print('✅ Kafka OK')"

# View last 50 logs
docker-compose logs --tail=50

# Check specific consumer
docker logs ingestion-app-events | grep ERROR

# Reset offset (start from beginning)
docker exec kafka kafka-consumer-groups --bootstrap-server kafka:9092 \
  --group app_events_consumer --reset-offsets --to-earliest --execute --topic topic_app_events
```

---

**Ready?** → See [README.md](README.md) for full documentation
