# 🌐 Web User Analytics - Product Design

## Overview

Web User Analytics provides comprehensive user behavior insights from web browsers and applications. Focused on web-specific metrics like page views, bounce rates, session tracking, and conversion funnels.

## Problem Statement

- How do we track user behavior across multiple pages and domains?
- What metrics define web application health?
- How do we identify drop-off points in user funnels?
- How do we attribute conversions across channels?

## Solution

Build a real-time analytics pipeline that:
1. Ingests events from JavaScript SDK
2. Reconstructs user sessions
3. Computes page-level and funnel metrics
4. Serves insights via REST APIs
5. Powers real-time dashboards

## Architecture

### Data Model

```
page_view
├── user_id (tracking ID)
├── session_id (30-min correlation)
├── page_id / page_url
├── referrer
├── event_timestamp
├── page_load_time_ms
├── device_type (desktop, mobile, tablet)
├── browser
├── region
└── properties (JSON)
```

### Event Types

- **page_view**: New page loaded
- **click**: Element clicked
- **scroll**: Scroll depth tracked
- **form_submit**: Form submission
- **video_play**: Video interaction
- **custom_event**: App-specific events
- **session_start**: New session initiated
- **session_end**: Session timeout/user left

### Layering Decision

**Bronze Layer**: Raw events, session enrichment  
**Silver Layer**: Session reconstruction, deduplication, path analysis  
**Gold Layer**: Aggregated page metrics, funnel conversions, attribution

### Processing Strategy

- **Real-time**: 5-minute aggregation (website traffic is faster)
- **Hourly**: Page performance, traffic sources
- **Daily**: Funnel analysis, retention, trend analysis

## Key Design Decisions

### 1. Session Definition: 30-Minute Timeout

**Decision**: Timeout after 30 minutes of inactivity

**Rationale**:
- Industry standard for web analytics
- Use last-click timestamp for detection
- Handles page refresh gracefully
- Balances accuracy vs data volume

### 2. Cross-Domain Tracking

**Decision**: Support optional cross-domain tracking

**Rationale**:
- Users may browse multiple domains
- Requires domain allowlist to be configured
- JavaScript SDK adds tracking parameters
- Merges into single user session

### 3. Bot Detection

**Decision**: Simple filter on user agent + behavior

**Rationale**:
- Remove obvious bot traffic
- Check user agent against known bots
- Flag suspicious behavior (zero scroll, instant navigation)
- Can improve with ML models later

### 4. Spark Streaming vs Flink

**Decision**: Spark Streaming

**Rationale**:
- Same as Mobile Analytics
- Familiar framework
- Integrates with Delta Lake
- Good throughput for web scale

### 5. Data Retention: 1 Year for Silver/Gold

**Decision**: 1 year retention for analytics

**Rationale**:
- YoY comparisons needed
- Bronze (90 days) for debugging
- 2-7 years for compliance
- Cost-effective archival for older data

## Data Quality Measures

1. **Schema Validation**: Avro schema enforcement
2. **Session Consistency**: All events within session OK
3. **Duplicate Detection**: Same event_id + timestamp
4. **Bot Filtering**: User agent + behavior rules
5. **Check Referrer**: Valid domain format
6. **Freshness**: Monitor event latency

## Performance Targets

- **Event ingestion latency**: <5 seconds
- **Session reconstruction**: <30 seconds
- **API response time**: <800ms (p99)
- **Availability**: 99.9%
- **Data accuracy**: 99.5% (for non-bot traffic)

## Security & Compliance

- **PII handling**: No page content captured, hashed user IDs
- **Data retention**: Configurable per region (GDPR)
- **Access control**: Role-based (viewer, analyst, admin)
- **Audit logging**: All query/export access logged
- **Encryption**: TLS for data in transit, at-rest encryption optional

## Future Extensions

1. **ML attribution**: Multi-touch attribution models
2. **Session replay**: Anonymous session playback
3. **Heatmaps**: Visual click/scroll heatmaps
4. **Real-time alerts**: Anomaly detection on traffic
5. **Predictive analytics**: Churn prediction per page
6. **A/B testing integration**: Statistical testing framework
