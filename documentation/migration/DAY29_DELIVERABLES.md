# Day 29 Deliverables - Guarded Decommission + Backup/Runbook/Rollback Snapshot

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY28_DELIVERABLES.md](DAY28_DELIVERABLES.md)

## 1) Runner + watcher Day 29

Runner Day 29:
- [../../shared/platform/migration_templates/day29_decommission_runner.py](../../shared/platform/migration_templates/day29_decommission_runner.py)

Watcher checklist Day 29:
- [../../shared/platform/migration_templates/day29_decommission_watcher.py](../../shared/platform/migration_templates/day29_decommission_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day29_decommission_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day29_decommission_guarded.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day29_decommission_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day29_decommission_hourly.sh)

Env profile:
- [../../infrastructure/docker/migration-day4/.env.day29.decommission.example](../../infrastructure/docker/migration-day4/.env.day29.decommission.example)

Cron template:
- [../../infrastructure/docker/migration-day4/scripts/day29_decommission_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day29_decommission_hourly.cron.example)

## 2) Rule guardrail Day 29

Day 29 chỉ được `DECOMMISSIONED_WITH_BACKUP` khi đồng thời PASS:
- Day 28 đã `FREEZE_LOCKED_REPORT_FINALIZED`
- Legacy cron/job/route/config đã được tháo dỡ hoặc vô hiệu hóa
- Backup config hoàn tất
- Runbook vận hành được finalize
- Rollback snapshot cuối được tạo
- Dry-run decommission pass

## 3) Báo cáo Day 29

- Decommission report: [reports/DAY29_DECOMMISSION_REPORT.json](reports/DAY29_DECOMMISSION_REPORT.json)
- Watcher report: [reports/DAY29_WATCHER_RESULT.json](reports/DAY29_WATCHER_RESULT.json)
- Trend report (24h): [reports/DAY29_DECOMMISSION_TREND_24H.json](reports/DAY29_DECOMMISSION_TREND_24H.json)

Trend runner:
- [../../shared/platform/migration_templates/day29_decommission_trend.py](../../shared/platform/migration_templates/day29_decommission_trend.py)

## 4) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day29_decommission_guarded.sh
bash infrastructure/docker/migration-day4/scripts/run_day29_decommission_hourly.sh
```

## 5) Trạng thái hiện tại

Theo dữ liệu hiện tại expected là `BLOCKED` cho đến khi Day 28 đạt `FREEZE_LOCKED_REPORT_FINALIZED` và tất cả hạng mục decommission/backups hoàn tất.
