# Day 30 Deliverables - Guarded Go-Live Closure

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY29_DELIVERABLES.md](DAY29_DELIVERABLES.md)

## 1) Runner + watcher Day 30

Runner Day 30:
- [../../shared/platform/migration_templates/day30_closure_runner.py](../../shared/platform/migration_templates/day30_closure_runner.py)

Watcher checklist Day 30:
- [../../shared/platform/migration_templates/day30_closure_watcher.py](../../shared/platform/migration_templates/day30_closure_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day30_closure_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day30_closure_guarded.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day30_closure_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day30_closure_hourly.sh)

Env profile:
- [../../infrastructure/docker/migration-day4/.env.day30.closure.example](../../infrastructure/docker/migration-day4/.env.day30.closure.example)

Cron template:
- [../../infrastructure/docker/migration-day4/scripts/day30_closure_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day30_closure_hourly.cron.example)

## 2) Rule guardrail Day 30

Day 30 chỉ được `GO_LIVE_CLOSED` khi đồng thời PASS:
- Day 29 đã `DECOMMISSIONED_WITH_BACKUP`
- Biên bản nghiệm thu kỹ thuật đã ký
- Lessons learned đã tổng kết và publish
- Phase tối ưu chi phí/hiệu năng đã kickoff

## 3) Báo cáo Day 30

- Closure report: [reports/DAY30_CLOSURE_REPORT.json](reports/DAY30_CLOSURE_REPORT.json)
- Watcher report: [reports/DAY30_WATCHER_RESULT.json](reports/DAY30_WATCHER_RESULT.json)
- Trend report (24h): [reports/DAY30_CLOSURE_TREND_24H.json](reports/DAY30_CLOSURE_TREND_24H.json)

Trend runner:
- [../../shared/platform/migration_templates/day30_closure_trend.py](../../shared/platform/migration_templates/day30_closure_trend.py)

## 4) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day30_closure_guarded.sh
bash infrastructure/docker/migration-day4/scripts/run_day30_closure_hourly.sh
```

## 5) Trạng thái hiện tại

Theo dữ liệu hiện tại expected là `BLOCKED` cho đến khi Day 29 hoàn tất decommission và toàn bộ hạng mục closure của Day 30 được xác nhận.
