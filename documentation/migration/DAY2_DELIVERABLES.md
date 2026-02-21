# Day 2 Deliverables - Data Contracts + Compare Rules + Report Format

Ngày thực hiện: 2026-02-21
Liên kết Day 1: [DAY1_DELIVERABLES.md](DAY1_DELIVERABLES.md)

## 1) Danh sách data contracts (schema event + schema bảng output)

## 1.1 Event contract - `web_user_analytics_event_v1`

### Required fields
- `event_id` (string, UUID)
- `user_id` (string)
- `session_id` (string)
- `event_type` (enum: `page_view`, `click`, `conversion`)
- `timestamp` (ISO-8601 UTC)
- `page_url` (string, valid URL)
- `page_path` (string)
- `browser` (string)
- `os` (string)
- `country` (string, ISO country code)

### Optional fields
- `page_title` (string)
- `user_agent` (string)
- `ip_address` (string)
- `device_type` (enum: `desktop`, `mobile`, `tablet`, `other`)
- `properties` (object)

### Contract rules
- `event_id` unique theo cửa sổ compare.
- `timestamp` phải timezone-aware UTC.
- `event_type` ngoài enum => reject.
- `page_url` không hợp lệ => reject hoặc quarantine.

---

## 1.2 Table contract - Bronze (`web_analytics_bronze`)
- Partition keys: `dt` (yyyy-mm-dd), `event_type`
- Required columns:
  - `event_id` string
  - `ingest_ts` timestamp (UTC)
  - `payload` string/json
  - `source` string
- Constraints:
  - `event_id` not null
  - `ingest_ts` not null

## 1.3 Table contract - Silver (`web_analytics_silver`)
- Required columns:
  - `event_id` string
  - `user_id` string
  - `session_id` string
  - `event_type` string
  - `event_ts` timestamp (UTC)
  - `page_path` string
  - `is_bot` boolean
  - `quality_score` double
- Constraints:
  - `event_id` unique
  - `event_ts` not null
  - `quality_score` in [0, 100]

## 1.4 Table contract - Gold (`web_analytics_gold_daily`)
- Grain: `dt, metric_name, dimension_key`
- Required columns:
  - `dt` date
  - `metric_name` string
  - `dimension_key` string
  - `metric_value` double
  - `updated_at` timestamp (UTC)
- Constraints:
  - PK logical: (`dt`, `metric_name`, `dimension_key`)
  - `metric_value` not null

## 1.5 Table contract - Operational KPIs (`operational_metrics_kpi_daily`)
- Required columns:
  - `dt` date
  - `pipeline_success_rate` double
  - `data_freshness_minutes` double
  - `api_p99_latency_ms` double
  - `data_quality_score` double
  - `overall_status` string (enum: `HEALTHY`, `WARNING`, `CRITICAL`, `UNHEALTHY`)
- Constraints:
  - `pipeline_success_rate`, `data_quality_score` in [0, 100]
  - `data_freshness_minutes`, `api_p99_latency_ms` >= 0

---

## 2) Rule so sánh kết quả legacy vs OSS

## 2.1 Rule bắt buộc (gating)
- **Schema compatibility**: 100% cột required tồn tại và đúng kiểu.
- **Primary-key mismatch**: <= 0.1% (theo PK logical của từng bảng).
- **Row count diff**: <= 0.5% theo từng bảng/partition `dt`.
- **Critical field null diff**: <= 0.2 điểm phần trăm cho field required.
- **Duplicate rate diff**: <= 0.1 điểm phần trăm.

## 2.2 Rule khuyến nghị (non-gating)
- **Numeric tolerance**: `abs(legacy - oss) <= 1e-6` hoặc theo ngưỡng metric.
- **Distribution drift** (metric_value): KS/PSI chỉ cảnh báo, không block ở tuần 1-2.
- **Latency compare**: p95/p99 OSS không tệ hơn >20% baseline.

## 2.3 Rule so sánh theo lớp
- **Bronze**: tập trung row count, schema, ingest latency.
- **Silver**: thêm uniqueness, null/duplicate, quarantine rate.
- **Gold/KPI**: thêm metric delta và status consistency.

## 2.4 Severity mapping
- `critical`: schema break, mất cột required, PK mismatch vượt ngưỡng.
- `high`: row count diff > 0.5%, null diff > ngưỡng.
- `medium`: numeric tolerance fail cục bộ.
- `low`: formatting drift, ordering khác nhưng dữ liệu tương đương.

---

## 3) Format output chuẩn để so sánh

## 3.1 JSON report (bắt buộc)
- File: `compare_report_<run_id>.json`
- Encoding: UTF-8
- Cấu trúc:

```json
{
  "run_id": "2026-02-21T12:00:00Z_001",
  "run_ts": "2026-02-21T12:00:00+00:00",
  "scope": {
    "products": ["web-user-analytics", "operational-metrics"],
    "tables": ["web_analytics_bronze", "web_analytics_silver", "web_analytics_gold_daily", "operational_metrics_kpi_daily"],
    "date_range": "2026-02-20..2026-02-21"
  },
  "summary": {
    "overall_status": "PASS",
    "critical_issues": 0,
    "high_issues": 1,
    "medium_issues": 2,
    "low_issues": 3
  },
  "table_results": [
    {
      "table": "web_analytics_silver",
      "status": "PASS",
      "checks": {
        "schema": {"status": "PASS"},
        "row_count": {"legacy": 1000000, "oss": 999200, "diff_pct": 0.08, "status": "PASS"},
        "pk_mismatch": {"mismatch_pct": 0.03, "status": "PASS"},
        "null_diff": {"diff_pct": 0.12, "status": "PASS"},
        "duplicate_diff": {"diff_pct": 0.04, "status": "PASS"}
      }
    }
  ],
  "issues": [
    {
      "severity": "high",
      "table": "operational_metrics_kpi_daily",
      "check": "row_count",
      "message": "Row count diff 0.62% > 0.5%",
      "suggested_action": "Recheck partition filter and late-arrival handling"
    }
  ]
}
```

## 3.2 Parquet output (khuyến nghị)
- Dataset: `compare_reports_parquet/`
- Partition: `run_date`, `table`, `severity`
- Mục tiêu: truy vấn trend mismatch và dashboard theo thời gian.

## 3.3 Naming & retention
- JSON: giữ 30 ngày.
- Parquet compare dataset: giữ 90 ngày.
- Với report có `critical`: lưu tối thiểu 180 ngày để audit.

---

## 4) Acceptance cho Ngày 2
- [x] Có danh sách contract cụ thể cho event + table chính trong scope Day 1.
- [x] Có compare rules định lượng và mapping severity.
- [x] Có format output chuẩn JSON + định hướng Parquet để theo dõi trend.

## 5) Handoff sang Ngày 3
- Tạo feature flags theo naming đã thống nhất.
- Bind compare job vào dual-run pipeline.
- Gắn logging marker `legacy/oss/dual-run` ở router và adapter.
