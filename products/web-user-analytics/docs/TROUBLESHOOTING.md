# 🔧 Web User Analytics - Troubleshooting Guide

## Common Issues & Solutions

### 1. High Consumer Lag

**Symptom**: Consumer lag > 5 minutes

**Causes**:
- Kafka broker is slow
- Consumer processing is bottlenecked
- Too many concurrent consumers

**Solutions**:

```bash
# Check consumer lag
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group web-analytics-consumer \
  --describe

# Scale up consumer instances (in Kubernetes)
kubectl scale deployment web-analytics-consumer --replicas=3

# Check Kafka broker health
kubectl logs kafka-0 -n kafka | grep -i error
```

**Prevention**:
- Monitor lag continuously (alert at >5 min)
- Right-size batch_size in config (currently 5000)
- Ensure Spark cluster has enough CPU/memory

---

### 2. Session Reconstruction Inaccuracy

**Symptom**: Sessions don't correlate properly, duplicate users

**Causes**:
- Session timeout too short (30 min default)
- Cross-domain tracking not configured
- Client-side tracking ID mismatch

**Check Traces**:

```python
# Verify session tracker logic
cd src/ingestion
python -m pytest test_session_tracking.py -v
```

**Solutions**:

```yaml
# In config/product_config.yaml
ingestion:
  session_timeout_minutes: 45  # Increase if needed
  cross_domain_tracking: true
  cross_domain_allowlist:
    - example.com
    - subdomain.example.com
```

**Prevention**:
- Review session logic with product team
- Validate against manual session traces
- Monitor session_reconstruction_accuracy metric

---

### 3. Page Load Time Metrics Incorrect

**Symptom**: Metrics show unrealistic page load times

**Causes**:
- Client-side measurement timing issues
- Network delays not captured
- Bot traffic inflating metrics

**Solutions**:

```python
# Filter out bot traffic
# In src/storage/silver_transforms.py
def remove_bot_traffic(df):
    return df.filter(~df.is_bot)

# Validate page load time range
def validate_page_load_time(df):
    return df.filter(
        (df.page_load_time_ms > 0) & 
        (df.page_load_time_ms < 60000)  # Max 60 seconds
    )
```

**Check Data Quality**:

```bash
# Run data quality checks
make quality-check

# Check bot traffic percentage
SELECT COUNT(*) as bot_events FROM web_events_silver 
WHERE is_bot = true AND event_date = CURRENT_DATE()
```

**Prevention**:
- Review bot detection rules
- Validate with RUM (Real User Monitoring) tools
- Compare with CDN metrics

---

### 4. Bounce Rate Anomalies

**Symptom**: Bounce rate suddenly high (>70%)

**Causes**:
- High bot traffic
- Page error (500s) causing quick exits
- Analytics code not loading properly

**Diagnose**:

```sql
-- Check for traffic from bots
SELECT is_bot, COUNT(*) FROM web_events_silver 
WHERE event_date = CURRENT_DATE() 
GROUP BY is_bot;

-- Check for page errors
SELECT DISTINCT page_url FROM page_views 
WHERE bounce_rate > 70% 
ORDER BY bounce_rate DESC;
```

**Solutions**:

1. **If bot traffic high**: Improve bot filtering
2. **If page errors**: Page team to investigate
3. **If SDK issue**: Check JavaScript SDK version

```bash
# Check JavaScript SDK version in GA
curl https://cdn.example.com/tracking.js | grep version
```

**Prevention**:
- Monitor bounce rate by page
- Alert on sudden >10% changes
- Review top bounce-rate pages weekly

---

### 5. Funnel Conversion Drop

**Symptom**: Funnel conversion rate drops significantly

**Causes**:
- Page redesign or changes
- Bug in conversion tracking
- External factor (ads turned off, etc.)

**Investigate**:

```python
# Check funnel step data
df = spark.sql("""
SELECT 
  funnel_step,
  event_date,
  COUNT(DISTINCT session_id) as sessions,
  COUNT(*) as events
FROM funnel_events
WHERE funnel_id = 'purchase_funnel'
  AND event_date >= DATE_SUB(CURRENT_DATE, 7)
GROUP BY funnel_step, event_date
ORDER BY event_date DESC, funnel_step
""")

# Look for anomalies
df.show()
```

**Solutions**:

- Check release notes for page changes
- Verify conversion tracking code on page
- Review traffic source changes
- Check for deployment issues

**Prevention**:
- Alert on >20% drop in any funnel step
- Track release dates alongside metrics
- A/B test page changes

---

### 6. Real-Time Data Delay

**Symptom**: Dashboards not updating in real-time

**Causes**:
- Streaming jobs lagging
- Kafka topics not getting events
- Cache not invalidating

**Debug**:

```bash
# Check if events are flowing on topic
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic topic_web_events \
  --max-messages 10

# Check Spark streaming job status
kubectl logs deployment/web-analytics-processor -n data | tail -50

# Check cache invalidation
redis-cli --scan --match "web_analytics*"
```

**Solutions**:

```python
# Force cache invalidation
from src.serving.cache_layer import invalidate_cache
invalidate_cache("all")

# Restart streaming jobs
kubectl rollout restart deployment/web-analytics-processor
```

**Prevention**:
- Monitor job lag metric
- Set up alerts for >5 min lag
- Have runbook for emergency restarts

---

### 7. API Response Time High

**Symptom**: P99 latency > 5 seconds

**Causes**:
- Large query results
- Insufficient cache hits
- Spark cluster overloaded

**Analyze**:

```bash
# Check API server logs
kubectl logs svc/web-analytics-api | grep duration_ms | sort -k2 -n | tail -20

# Check query complexity
SELECT 
  query_id, 
  execution_time_ms,
  row_count
FROM query_logs
WHERE execution_time_ms > 5000
ORDER BY execution_time_ms DESC
LIMIT 10
```

**Solutions**:

```python
# Add caching for common queries
@cache(ttl=3600)
def get_daily_metrics(page_id, date):
    return spark.sql(f"""
    SELECT * FROM gold_metrics 
    WHERE page_id = '{page_id}' AND date = '{date}'
    """)

# Optimize query
SELECT page_id, COUNT(*) as pv
FROM page_views
WHERE event_date = CURRENT_DATE()
GROUP BY page_id
-- Add query hints if needed
```

**Prevention**:
- Monitor API latency percentiles
- Pre-compute common aggregations
- Add Redis caching layer
- Right-size resource limits

---

### 8. Storage Growing Too Fast

**Symptom**: Delta Lake storage exceeds quota

**Causes**:
- Too many small files
- Old partitions not cleaned up
- Uncompressed data

**Check**:

```python
from shared.core.utils import DeltaUtils

# Check table size
delta = DeltaUtils()
size = delta.get_table_size("web_events_bronze")
print(f"Total size: {size / 1e9:.2f} GB")

# Show partitions
partitions = delta.list_partitions("web_events_bronze")
print(f"Partition count: {len(partitions)}")
```

**Solutions**:

```python
# Vacuum old files (keep 7 days)
delta.vacuum("web_events_bronze", retention_days=7)

# Compact files
delta.optimize("web_events_bronze")

# Z-order by common filter columns
delta.optimize_z_order("web_events_silver", ["user_id", "page_id"])
```

**Prevention**:
- Schedule regular VACUUM jobs
- Monitor table size metrics
- Set retention policies in config

---

### 9. Data Quality Checks Failing

**Symptom**: Quality check failures in logs

**Causes**:
- Null values in required fields
- Invalid event types
- Out-of-range timestamps

**Debug**:

```python
# Run quality checks manually
from src.monitoring.quality_checks import QualityChecker

checker = QualityChecker()
results = checker.run_all_checks("web_events_silver")

for check, passed, details in results:
    if not passed:
        print(f"FAIL: {check}")
        print(f"  Details: {details}")
```

**Solutions**:

```python
# Fix data in pipeline
def clean_events(df):
    return df.filter(
        df.user_id.is_not_null()
    ).filter(
        df.event_type.isin(['page_view', 'click', ...])
    ).filter(
        df.event_timestamp.between(
            timestamp('2024-01-01'),
            timestamp('2099-12-31')
        )
    )
```

---

### 10. Permissions/Access Issues

**Symptom**: User sees "Access Denied" errors

**Causes**:
- Role not assigned
- API token expired
- Insufficient permissions

**Check User Role**:

```bash
# Check user's assigned role
SELECT user_id, role, created_at 
FROM access_control.user_roles 
WHERE user_id = 'user_123'

# Check role permissions
SELECT * FROM access_control.roles WHERE name = 'analyst'
```

**Solutions**:

```bash
# Grant analyst role to user
UPDATE access_control.user_roles 
SET role = 'analyst', updated_at = NOW()
WHERE user_id = 'user_123'

# Or create new token (if token expired)
POST /api/v1/auth/refresh-token
```

---

## Quick Troubleshooting Checklist

- [ ] Check consumer lag
- [ ] Verify Kafka broker health
- [ ] Check Spark cluster CPU/memory
- [ ] Review recent deployments
- [ ] Check bot traffic %
- [ ] Validate data quality checks
- [ ] Review API error logs
- [ ] Check storage usage
- [ ] Verify user permissions
- [ ] Check cache hit rate

---

## Getting Help

**Slack**: #web-analytics-incidents  
**PagerDuty**: @team-web  
**Runbook**: [This document]  
**On-call**: Check rotation schedule  

