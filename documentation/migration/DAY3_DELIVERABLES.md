# Day 3 Deliverables - Feature Flags + Ports/Adapters + Logging Markers

Ngày thực hiện: 2026-02-21
Phụ thuộc từ Day 1/2:
- [DAY1_DELIVERABLES.md](DAY1_DELIVERABLES.md)
- [DAY2_DELIVERABLES.md](DAY2_DELIVERABLES.md)

## 1) Feature flags migration đã chuẩn hóa

Các biến môi trường dùng cho migration:
- `USE_OSS_INGESTION`
- `USE_OSS_QUALITY`
- `USE_OSS_SERVING`
- `READ_FROM_OSS_SERVING`
- `DUAL_RUN_ENABLED`
- `DUAL_RUN_COMPARE_ENABLED`

Định nghĩa chính thức tại:
- [../../shared/platform/migration_templates/feature_flags.py](../../shared/platform/migration_templates/feature_flags.py)

## 2) Interface/ports + adapter cho code cũ/mới

### 2.1 Ports
- [../../shared/platform/migration_templates/ports.py](../../shared/platform/migration_templates/ports.py)
  - `IngestionPort`
  - `QualityPort`
  - `ServingPort`

### 2.2 Adapters
- [../../shared/platform/migration_templates/adapters.py](../../shared/platform/migration_templates/adapters.py)
  - `LegacyIngestionAdapter`, `OSSIngestionAdapter`
  - `LegacyQualityAdapter`, `OSSQualityAdapter`
  - `LegacyServingAdapter`, `OSSServingAdapter`

### 2.3 Router
- [../../shared/platform/migration_templates/router.py](../../shared/platform/migration_templates/router.py)
  - Chọn path legacy/oss theo flags
  - Hỗ trợ `dual-run` cho ingestion/quality/serving
  - Hỗ trợ `read_from_oss_serving`

## 3) Logging marker cho từng path

Marker chuẩn đã áp dụng:
- Legacy path: `migration.path=legacy`
- OSS path: `migration.path=oss`
- Dual-run path: `migration.path=dual-run`

Ví dụ log fields:
- `component=ingestion|quality|serving`
- `stage=ingestion|quality|serving`
- `compare ...` khi bật `DUAL_RUN_COMPARE_ENABLED=true`

## 4) Cấu hình môi trường mẫu

File mẫu đã tạo:
- [../../shared/platform/migration_templates/migration.env.example](../../shared/platform/migration_templates/migration.env.example)

Suggested rollout:
1. Legacy only: mọi flag OSS = false.
2. Dual-run compare: `DUAL_RUN_ENABLED=true`, read vẫn từ legacy.
3. Read switch canary: `READ_FROM_OSS_SERVING=true` theo tỷ lệ.
4. OSS primary: bật `USE_OSS_*` tương ứng và giữ fallback ngắn hạn.

## 5) Acceptance Day 3
- [x] Có bộ feature flags chuẩn, thống nhất naming.
- [x] Có ports/adapters/router để tách legacy và OSS path.
- [x] Có marker log `legacy/oss/dual-run` để truy vết và so sánh.

## 6) Handoff Day 4
- Dựng môi trường OSS tối thiểu (Kafka/Airflow/Redis/Prometheus).
- Gắn secret/config qua env + secret manager.
- Verify healthcheck end-to-end trên staging.
