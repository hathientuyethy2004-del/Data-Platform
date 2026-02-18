# 📊 Web User Analytics - KPI Definitions

## Core Metrics

### 1. Unique Visitors (UV)
**Definition**: Distinct users who viewed at least one page

**Formula**: COUNT(DISTINCT user_id) WHERE event_date = DATE

**Calculation**: Daily at 2 AM

**SLA**: Baseline (no target, trending metric)

---

### 2. Page Views (PV)
**Definition**: Total page impressions

**Formula**: COUNT(*) WHERE event_type = 'page_view' AND event_date = DATE

**Calculation**: Real-time + daily aggregation

**SLA**: >1M PV/day for top pages

---

### 3. Bounce Rate
**Definition**: % of sessions with only one page view

**Formula**: (Sessions with 1 PV) / (Total sessions)

**Calculation**: Throughout day, finalized daily

**Target**: <50% for content pages, <30% for product pages

**Alert**: If >60%, possible traffic quality issue

---

### 4. Average Session Duration
**Definition**: Mean time spent per session

**Formula**: AVG(session_end_time - session_start_time)

**Unit**: Seconds

**Target**:
- Homepage: 30-60 seconds
- Content pages: 60-180 seconds
- Product pages: 120-300 seconds

---

### 5. Sessions Per User
**Definition**: Average sessions per user per day

**Formula**: COUNT(DISTINCT session_id) / COUNT(DISTINCT user_id)

**Target**: 1.2 - 1.8 (returning users)

---

### 6. Page Load Time
**Definition**: 50th, 90th, 99th percentile page load time

**Formula**: PERCENTILE(page_load_time_ms, [50, 90, 99])

**Target**:
- p50: <1000ms
- p90: <2000ms
- p99: <5000ms

**Alert**: If p90 > 3000ms

---

### 7. Conversion Rate
**Definition**: % of sessions that completed a goal

**Formula**: (Sessions with conversion) / (Total sessions)

**Calculation**: Per funnel/page

**Target**: Varies by funnel (typically 2-10%)

---

### 8. Traffic by Source
**Definition**: Breakdown of traffic by referrer

**Categories**:
- Direct
- Organic (search)
- Paid (ads)
- Social
- Referral
- Email
- Dark traffic

**Target**: Organic >40%, Direct >20%

---

## Device & Browser Metrics

### 9. Mobile vs Desktop Split
**Definition**: % of traffic by device type

**Formula**: (Mobile sessions) / (Total sessions)

**Target**: 50-70% mobile (varies by industry)

---

### 10. Top Browsers
**Definition**: Table of browser usage

**Includes**: Chrome, Safari, Firefox, Edge, others

**Calculation**: Daily

---

## Geographic Metrics

### 11. Top Regions/Countries
**Definition**: Traffic breakdown by geography

**Granularity**: Country, then Region

**Calculation**: Real-time

---

## Engagement Metrics

### 12. Scroll Depth
**Definition**: How far users scroll down pages

**Percentiles**: p25, p50, p75, p95 (% of page scrolled)

**Target**: p50 >75% (users seeing most content)

---

### 13. Click-Through Rate (CTR)
**Definition**: % of users who click specific elements

**Formula**: (Clicks on element) / (Page views)

**Per Element**: Track individually

**Target**: 5-15% CTA buttons

---

### 14. Form Completion Rate
**Definition**: % of form starts that complete

**Formula**: (Form submissions) / (Form focused events)

**Target**: >80% (high abandonment indicates form issue)

---

## Funnel Metrics

### 15. Funnel Conversion Rate
**Definition**: Percentage reaching each step

**Steps**: 
1. Landing page (100%)
2. Signup (e.g., 40%)
3. Email verified (e.g., 35%)
4. Profile complete (e.g., 30%)
5. First purchase (e.g., 5%)

**Calculation**: Daily

**Alert**: If step drops >20% vs previous day

---

### 16. Funnel Drop-off
**Definition**: Where users abandon funnel

**Formula**: (Users at step N) - (Users at step N+1)

**Focus**: Largest drop-off point for optimization

---

## Quality Metrics

### 17. Data Freshness
**Definition**: Lag between event occurrence and availability

**Target**: <5 minutes for 95% of events

**Alert**: If >10 minutes

---

### 18. Bot Traffic %
**Definition**: Percentage of traffic flagged as bots

**Formula**: (Bot events) / (Total events)

**Target**: <3%

**Alert**: If >5%

---

## Composite KPIs

### 19. Engagement Score
**Definition**: Composite of bounce rate, session duration, pages per session

**Formula**: (1 - Bounce Rate) × (Session Duration / Target) × (Pages per Session / 2)

**Range**: 0-100

**Target**: >60

---

### 20. Traffic Health
**Definition**: Overall quality of traffic to site

**Formula**: (100 - Bot%) × (Page Load Time Health) × (Visitor Retention)

**Target**: >70

