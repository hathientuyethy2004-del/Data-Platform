# Day 8 Deliverables - Canary 10% (Write/Load OSS) + Legacy Read + Initial Monitoring

Ngày thực hiện: 2026-02-21
Phụ thuộc từ Day 5-7:
- [DAY5_DELIVERABLES.md](DAY5_DELIVERABLES.md)
- [DAY6_DELIVERABLES.md](DAY6_DELIVERABLES.md)
- [DAY7_DELIVERABLES.md](DAY7_DELIVERABLES.md)

## 1) Bật canary 10% write/load vào path OSS

Profile Day 8:
- [../../infrastructure/docker/migration-day4/.env.day8.canary10.example](../../infrastructure/docker/migration-day4/.env.day8.canary10.example)

Điểm chính:
- `OSS_CANARY_WRITE_PERCENT=10`
- `OSS_CANARY_MODE=shadow_write`
- `OSS_CANARY_HASH_KEY=event_id`

## 2) Giữ read path từ legacy

Cấu hình read path:
- `READ_FROM_OSS_SERVING=false`

Kiểm tra tự động trong report Day 8:
- `checks.read_path_stays_legacy.status=PASS`

## 3) Theo dõi dashboard SLO + chất lượng dữ liệu (snapshot Day 8)

Runner Day 8:
- [../../shared/platform/migration_templates/day8_canary_runner.py](../../shared/platform/migration_templates/day8_canary_runner.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day8_canary_setup.sh](../../infrastructure/docker/migration-day4/scripts/run_day8_canary_setup.sh)

Script theo dõi theo giờ (latest + history + trend 24h):
- [../../infrastructure/docker/migration-day4/scripts/run_day8_canary_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day8_canary_hourly.sh)
- [../../infrastructure/docker/migration-day4/scripts/day8_canary_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day8_canary_hourly.cron.example)

Báo cáo Day 8:
- [reports/DAY8_CANARY_STATUS.json](reports/DAY8_CANARY_STATUS.json)
- [reports/DAY8_CANARY_TREND_24H.json](reports/DAY8_CANARY_TREND_24H.json)

Kết quả chạy hiện tại:
- `summary.status`: `PASS`
- `day8_canary_ready`: `true`
- Canary config/legacy-read checks: `PASS`

## 4) Acceptance Day 8
- [x] Canary 10% write/load OSS được cấu hình và verify.
- [x] Read path giữ legacy và có check tự động.
- [x] Có snapshot monitoring SLO/quality ban đầu cho Day 8.

## 5) Handoff Day 9
- Duy trì chạy kiểm Day 8 theo giờ/chu kỳ và theo dõi trend.
- Theo dõi biến động latency/error/data-quality trong cửa sổ quan sát mở rộng.
- Chuẩn bị tăng canary theo tiêu chí Day 10.
