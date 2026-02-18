# 🔌 Mobile User Analytics - API Reference

## Base URL

```
https://api.platform.example.com/mobile-analytics/v1
```

## Authentication

All endpoints require Bearer token:

```
Authorization: Bearer {token}
```

---

## Endpoints

### 1. Get User Summary

```http
GET /users/{user_id}/summary
```

**Response:**
```json
{
  "user_id": "user_123",
  "first_seen": "2024-01-15T10:30:00Z",
  "last_seen": "2024-02-18T14:45:00Z",
  "total_events": 2345,
  "total_sessions": 156,
  "avg_session_length": 456,
  "app_versions": ["1.2.0", "1.3.0"],
  "devices": ["iPhone13", "iPhone14"]
}
```

### 2. Get Daily Metrics

```http
GET /metrics/daily?date=2024-02-18
```

**Response:**
```json
{
  "date": "2024-02-18",
  "dau": 1250000,
  "mau": 4500000,
  "crash_rate": 0.32,
  "avg_session_length": 487,
  "new_users": 85000,
  "d1_retention": 0.42
}
```

### 3. Execute Query

```http
POST /query
```

**Body:**
```json
{
  "sql": "SELECT user_id, COUNT(*) as events FROM app_events WHERE event_date = CAST(now() AS DATE) GROUP BY user_id LIMIT 100"
}
```

**Response:**
```json
{
  "query_id": "q_abc123",
  "status": "completed",
  "rows": [...],
  "execution_time_ms": 1234
}
```

### 4. Get Cohort Analysis

```http
GET /cohorts/{cohort_id}
```

---

## Rate Limiting

- **Limit**: 1000 requests/minute
- **Header**: `X-RateLimit-Remaining`
- **Status Code**: 429 (Too Many Requests)

---

## Error Handling

```json
{
  "error": {
    "code": "INVALID_DATE",
    "message": "Date must be in YYYY-MM-DD format",
    "timestamp": "2024-02-18T10:30:00Z"
  }
}
```

