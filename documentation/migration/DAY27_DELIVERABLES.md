# Day 27 Deliverables - Full Regression + Performance + SLO/Audit Validation

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY25_26_DELIVERABLES.md](DAY25_26_DELIVERABLES.md)

## 1) Runner + watcher Day 27

Runner Day 27:
- [../../shared/platform/migration_templates/day27_validation_runner.py](../../shared/platform/migration_templates/day27_validation_runner.py)

Watcher checklist Day 27:
- [../../shared/platform/migration_templates/day27_validation_watcher.py](../../shared/platform/migration_templates/day27_validation_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day27_validation_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day27_validation_guarded.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day27_validation_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day27_validation_hourly.sh)

Env profile:
- [../../infrastructure/docker/migration-day4/.env.day27.validation.example](../../infrastructure/docker/migration-day4/.env.day27.validation.example)

Cron template:
- [../../infrastructure/docker/migration-day4/scripts/day27_validation_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day27_validation_hourly.cron.example)

## 2) Rule guardrail Day 27

Day 27 validation chỉ được `VALIDATED_FOR_FREEZE` khi đồng thời PASS:
- Day 25-26 đã `READ_PATH_100_LEGACY_DRAINING`
- Full regression suite pass
- Performance suite pass
- Performance guardrails: `p95 <= 500ms`, `p99 <= 1200ms`, `error_rate < 1%`
- SLO dashboard pass
- Alert verification pass
- Audit logs verification pass

## 3) Báo cáo Day 27

- Validation report: [reports/DAY27_VALIDATION_REPORT.json](reports/DAY27_VALIDATION_REPORT.json)
- Watcher report: [reports/DAY27_WATCHER_RESULT.json](reports/DAY27_WATCHER_RESULT.json)
- Trend report (24h): [reports/DAY27_VALIDATION_TREND_24H.json](reports/DAY27_VALIDATION_TREND_24H.json)

Trend runner:
- [../../shared/platform/migration_templates/day27_validation_trend.py](../../shared/platform/migration_templates/day27_validation_trend.py)

## 4) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day27_validation_guarded.sh
bash infrastructure/docker/migration-day4/scripts/run_day27_validation_hourly.sh
```

## 5) Trạng thái hiện tại

Theo dữ liệu hiện tại expected là `BLOCKED` cho đến khi Day 25-26 đạt `READ_PATH_100_LEGACY_DRAINING` và toàn bộ suite Day 27 đều pass.
