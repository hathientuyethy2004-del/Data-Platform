# 🔌 Web User Analytics - API Reference

## Base URL

```
https://api.platform.example.com/web-analytics/v1
```

## Authentication

All endpoints require Bearer token:

```
Authorization: Bearer {token}
```

---

## Endpoints

### 1. Get Page Metrics

```http
GET /pages/{page_id}/metrics?date_from=2024-02-01&date_to=2024-02-18
```

**Response:**
```json
{
  "page_id": "page_123",
  "page_url": "/products",
  "date_from": "2024-02-01",
  "date_to": "2024-02-18",
  "metrics": {
    "page_views": 150000,
    "unique_visitors": 45000,
    "avg_session_duration": 187,
    "bounce_rate": 32.4,
    "conversion_rate": 2.8,
    "avg_page_load_time_ms": 1234
  }
}
```

### 2. Get Funnel Conversion

```http
GET /funnels/{funnel_id}/conversion?date=2024-02-18
```

**Response:**
```json
{
  "funnel_id": "purchase_funnel",
  "date": "2024-02-18",
  "steps": [
    {
      "step": 1,
      "name": "Landing Page",
      "users": 100000,
      "conversion_rate": 100.0
    },
    {
      "step": 2,
      "name": "Product View",
      "users": 45000,
      "conversion_rate": 45.0,
      "drop_off": 55000
    },
    {
      "step": 3,
      "name": "Add to Cart",
      "users": 12000,
      "conversion_rate": 12.0,
      "drop_off": 33000
    },
    {
      "step": 4,
      "name": "Checkout",
      "users": 3000,
      "conversion_rate": 3.0,
      "drop_off": 9000
    }
  ]
}
```

### 3. Get Session Details

```http
GET /sessions/{session_id}
```

**Response:**
```json
{
  "session_id": "sess_abc123",
  "user_id": "user_456",
  "start_time": "2024-02-18T10:30:00Z",
  "end_time": "2024-02-18T10:45:00Z",
  "duration_seconds": 900,
  "page_count": 8,
  "event_count": 45,
  "referrer": "google.com",
  "device_type": "mobile",
  "browser": "Chrome",
  "region": "US-CA",
  "pages_visited": [
    {
      "page_id": "page_123",
      "page_url": "/products",
      "time_on_page": 120,
      "scroll_depth": 85
    }
  ],
  "events": [...]
}
```

### 4. Get User Journey

```http
GET /users/{user_id}/journey?limit=10
```

**Response:**
```json
{
  "user_id": "user_456",
  "first_seen": "2024-01-15T10:30:00Z",
  "last_seen": "2024-02-18T14:45:00Z",
  "total_sessions": 24,
  "total_events": 1250,
  "total_conversions": 3,
  "sessions": [
    {
      "session_id": "sess_abc123",
      "date": "2024-02-18",
      "duration_seconds": 900,
      "pages": 8,
      "conversion": true
    }
  ]
}
```

### 5. Execute Custom Query

```http
POST /query
```

**Body:**
```json
{
  "sql": "SELECT page_id, COUNT(*) as pv, COUNT(DISTINCT user_id) as uv FROM page_views WHERE event_date = CAST(now() AS DATE) GROUP BY page_id ORDER BY pv DESC LIMIT 10"
}
```

**Response:**
```json
{
  "query_id": "q_xyz789",
  "status": "completed",
  "execution_time_ms": 2500,
  "rows": [
    {
      "page_id": "page_123",
      "pv": 45000,
      "uv": 12000
    }
  ],
  "row_count": 1
}
```

### 6. Get Traffic Sources

```http
GET /traffic-sources?date=2024-02-18
```

**Response:**
```json
{
  "date": "2024-02-18",
  "total_sessions": 125000,
  "sources": [
    {
      "source": "direct",
      "sessions": 50000,
      "percentage": 40.0,
      "bounce_rate": 25.5
    },
    {
      "source": "organic",
      "sessions": 55000,
      "percentage": 44.0,
      "bounce_rate": 35.2
    },
    {
      "source": "paid",
      "sessions": 15000,
      "percentage": 12.0,
      "bounce_rate": 28.1
    }
  ]
}
```

### 7. Get Device Breakdown

```http
GET /devices?date=2024-02-18
```

**Response:**
```json
{
  "date": "2024-02-18",
  "total_sessions": 125000,
  "devices": [
    {
      "device_type": "mobile",
      "sessions": 75000,
      "percentage": 60.0,
      "avg_session_duration": 420,
      "bounce_rate": 38.5
    },
    {
      "device_type": "desktop",
      "sessions": 45000,
      "percentage": 36.0,
      "avg_session_duration": 780,
      "bounce_rate": 25.2
    },
    {
      "device_type": "tablet",
      "sessions": 5000,
      "percentage": 4.0,
      "avg_session_duration": 600,
      "bounce_rate": 32.0
    }
  ]
}
```

### 8. Get Page Performance

```http
GET /pages/{page_id}/performance?date=2024-02-18
```

**Response:**
```json
{
  "page_id": "page_123",
  "date": "2024-02-18",
  "page_load_time": {
    "p50_ms": 850,
    "p90_ms": 1800,
    "p99_ms": 4200,
    "avg_ms": 1234
  },
  "metrics": {
    "page_views": 45000,
    "bounce_rate": 32.4,
    "avg_time_on_page": 187
  }
}
```

---

## Rate Limiting

- **Limit**: 2000 requests/minute
- **Header**: `X-RateLimit-Remaining`
- **Status Code**: 429 (Too Many Requests)

---

## Pagination

For endpoints returning large datasets:

```
GET /query?limit=100&offset=0
```

---

## Error Handling

```json
{
  "error": {
    "code": "INVALID_DATE_RANGE",
    "message": "Date range must be within last 2 years",
    "timestamp": "2024-02-18T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

---

## Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| INVALID_DATE_RANGE | 400 | Date range invalid |
| INVALID_PAGE_ID | 404 | Page not found |
| INVALID_FUNNEL_ID | 404 | Funnel not found |
| UNAUTHORIZED | 401 | Invalid token |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |

