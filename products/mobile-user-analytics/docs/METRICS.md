# 📊 Mobile User Analytics - KPI Definitions

## Core Metrics

### 1. Daily Active Users (DAU)
**Definition**: Unique users who generated at least one event

**Formula**: COUNT(DISTINCT user_id) WHERE event_date = DATE

**Calculation**: Daily at 2 AM

**SLA**: >1M DAU

---

### 2. Monthly Active Users (MAU)
**Definition**: Unique users in last 28 days

**Formula**: COUNT(DISTINCT user_id) WHERE event_date >= DATE_SUB(DATE, 28)

**Calculation**: Daily at 2 AM

---

### 3. Session Length
**Definition**: Average time between first and last event in a session

**Formula**: AVG(session_end_time - session_start_time)

**Unit**: Seconds

**Targets**:
- iOS: >600 seconds
- Android: >500 seconds

---

### 4. Day 1 Retention
**Definition**: % of users active on day 2 after install

**Formula**: (Active users on day 2) / (New users on day 1)

**Target**: >40%

---

### 5. Day 7 Retention
**Definition**: % of users active 7 days after install

**Target**: >20%

---

### 6. Day 30 Retention
**Definition**: % of users active 30 days after install

**Target**: >10%

---

### 7. Crash Rate
**Definition**: (Crash events) / (App sessions)

**Target**: <0.5%

**Alerting**: If >1%, page on-call

---

### 8. App Version Adoption
**Definition**: % of DAU on latest version

**Formula**: (DAU on latest version) / (Total DAU)

**Target**: >80%

---

## Streaming Metrics

### Real-time Event Throughput
- **Metric**: Events per second
- **Calculation**: Every 10 seconds
- **Alert threshold**: <80% of baseline

### Consumer Lag
- **Metric**: Messages behind in Kafka topic
- **Target**: <1 minute
- **Alert threshold**: >5 minutes

## Composite KPIs

### Engagement Score
**Formula**: (DAU / MAU) × 100

**Target**: >25%

### Health Score
**Formula**: (100 - Crash Rate) × Day 30 Retention × App Version Adoption

**Target**: >60%

