# Day 15 Deliverables - Guarded Scale-Up to 50%

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY14_DELIVERABLES.md](DAY14_DELIVERABLES.md)

## 1) Runner + watcher Day 15

Runner Day 15:
- [../../shared/platform/migration_templates/day15_scale_runner.py](../../shared/platform/migration_templates/day15_scale_runner.py)

Watcher checklist Day 15-16:
- [../../shared/platform/migration_templates/day15_scale_watcher.py](../../shared/platform/migration_templates/day15_scale_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day15_scale_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day15_scale_guarded.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day15_compare_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day15_compare_hourly.sh)
- [../../infrastructure/docker/migration-day4/scripts/day15_compare_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day15_compare_hourly.cron.example)
- [../../infrastructure/docker/migration-day4/scripts/check_migration_cron_health.sh](../../infrastructure/docker/migration-day4/scripts/check_migration_cron_health.sh)

Env profile:
- [../../infrastructure/docker/migration-day4/.env.day15.scale50.example](../../infrastructure/docker/migration-day4/.env.day15.scale50.example)

## 2) Rule guardrail Day 15

Scale lên 50% chỉ được áp dụng khi đồng thời PASS:
- Day 14 Gate 2 `PASS` + `approve_scale_week3=true`
- Target Day 15 đúng 50%
- Bước tăng theo nấc an toàn (từ >=20% lên tối đa +30%)
- `DUAL_RUN_COMPARE_HOURLY=true`
- Read path vẫn từ legacy (`READ_FROM_OSS_SERVING=false`)

## 3) Báo cáo Day 15

- Scale report: [reports/DAY15_SCALE_REPORT.json](reports/DAY15_SCALE_REPORT.json)
- Watcher report: [reports/DAY15_WATCHER_RESULT.json](reports/DAY15_WATCHER_RESULT.json)
- Hourly trend report: [reports/DAY15_COMPARE_TREND_24H.json](reports/DAY15_COMPARE_TREND_24H.json)
- Cron health status JSON: [reports/MIGRATION_CRON_HEALTH_STATUS.json](reports/MIGRATION_CRON_HEALTH_STATUS.json)
- Cron health panel spec (BI key mapping): [reports/MIGRATION_CRON_HEALTH_PANEL_SPEC.json](reports/MIGRATION_CRON_HEALTH_PANEL_SPEC.json)
- Cron health flattened row (BI ingest-ready): [reports/MIGRATION_CRON_HEALTH_PANEL_ROW.json](reports/MIGRATION_CRON_HEALTH_PANEL_ROW.json)
- Hourly history snapshots: `reports/history/DAY15_SCALE_REPORT_*.json`

Trend runner:
- [../../shared/platform/migration_templates/day15_compare_trend.py](../../shared/platform/migration_templates/day15_compare_trend.py)

## 4) Trạng thái hiện tại

Với trạng thái Day 14 hiện `NO_GO`, Day 15 expected là `BLOCKED`.

## 5) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day15_scale_guarded.sh
```

Khi Day 14 chuyển `PASS`, script sẽ tự:
- áp dụng scale lên 50%
- đồng bộ checklist Day 15-16
- copy env active sang `.env.day15.active`
