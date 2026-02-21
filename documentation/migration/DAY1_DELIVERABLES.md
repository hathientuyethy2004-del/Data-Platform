# Day 1 Deliverables - Migration Open Source

Ngày thực hiện: 2026-02-21

## 1) Scope migration đã chốt

### 1.1 Dịch vụ trong phạm vi (Phase 1 - 30 ngày)
- `products/web-user-analytics`
- `products/operational-metrics`

### 1.2 Pipeline trong phạm vi
- Ingestion events -> Validation -> Session/Quality -> Serving query
- SLA/KPI aggregation path của `operational-metrics`

### 1.3 Bảng/layer dữ liệu trong phạm vi
- Bronze/Silver/Gold cho web analytics
- KPI output tables cho operational metrics

### 1.4 Endpoint trong phạm vi
- `web-user-analytics` serving query path (`/query`) + health endpoint
- `operational-metrics` health/SLA reporting endpoints

### 1.5 Ngoài phạm vi Phase 1
- Re-architecture toàn bộ `products/compliance-auditing`
- Multi-region active-active deployment
- Realtime serving với latency sub-second chuyên biệt (Pinot/Druid)

---

## 2) KPI migration đã chốt

## 2.1 Runtime/SLA
- Query p95 latency: <= 1200ms
- Query p99 latency: <= 2000ms
- Error rate API: <= 0.5%
- Uptime dịch vụ core: >= 99.5% trong giai đoạn migration

## 2.2 Data quality
- Row count diff (legacy vs OSS): <= 0.5%
- Null rate diff: <= 0.2 điểm phần trăm
- Duplicate rate diff: <= 0.1 điểm phần trăm
- Schema compatibility checks: 100% pass cho contract bắt buộc

## 2.3 Throughput/processing
- Throughput ingestion không thấp hơn 90% baseline
- Batch completion time không vượt quá +20% baseline

## 2.4 Error budget & rollback trigger
- Error budget theo ngày: 0.5%
- Rollback nếu:
  - Error rate > 1.5% trong 10 phút liên tiếp, hoặc
  - Data mismatch critical vượt ngưỡng đã định, hoặc
  - p99 latency > 2500ms trong 15 phút liên tiếp

---

## 3) Owner matrix đã chốt

| Hạng mục | Owner chính | Backup | Trách nhiệm chính |
|---|---|---|---|
| Ingestion (Kafka/bridge) | Data Engineer | Backend Engineer | Event contracts, ingest reliability, retry/idempotency |
| Processing (Spark/Airflow) | Data Engineer | Tech Lead | Batch logic, schedule, SLA jobs |
| Serving (FastAPI/Redis) | Backend Engineer | Data Engineer | Query path, auth/rate-limit, cache strategy |
| QA/Data Compare | QA/Analytics | Data Engineer | Baseline compare, mismatch report, regression |
| Platform/Observability | Platform/DevOps | Tech Lead | K8s/runtime, alerts, dashboard, on-call readiness |
| Governance/Cutover | Tech Lead | Platform/DevOps | Gate approvals, rollback decision, release sign-off |

---

## 4) Baseline & Gate-1 input đã chuẩn bị
- Đã có checklist 30 ngày tại [MIGRATION_CHECKLIST_30_DAYS.md](MIGRATION_CHECKLIST_30_DAYS.md)
- Đã chốt stack mục tiêu (team nhỏ): Kafka + Airflow + Spark + FastAPI + Redis + Prometheus/Grafana
- Đã có template adapter để bắt đầu tách legacy/OSS:
  - [../../shared/platform/migration_templates/ports.py](../../shared/platform/migration_templates/ports.py)
  - [../../shared/platform/migration_templates/router.py](../../shared/platform/migration_templates/router.py)

## 5) Chuyển giao sang Ngày 2
Ngày 2 sẽ làm 3 việc:
1. Lập data contracts chi tiết theo event/table.
2. Định nghĩa rule compare tự động (row/checksum/null/dup).
3. Chốt format output compare report (JSON + summary table).
