# Day 28 Deliverables - Guarded Freeze 24h + Post-Cutover Report Closure

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY27_DELIVERABLES.md](DAY27_DELIVERABLES.md)

## 1) Runner + watcher Day 28

Runner Day 28:
- [../../shared/platform/migration_templates/day28_freeze_runner.py](../../shared/platform/migration_templates/day28_freeze_runner.py)

Watcher checklist Day 28:
- [../../shared/platform/migration_templates/day28_freeze_watcher.py](../../shared/platform/migration_templates/day28_freeze_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day28_freeze_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day28_freeze_guarded.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day28_freeze_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day28_freeze_hourly.sh)

Env profile:
- [../../infrastructure/docker/migration-day4/.env.day28.freeze.example](../../infrastructure/docker/migration-day4/.env.day28.freeze.example)

Cron template:
- [../../infrastructure/docker/migration-day4/scripts/day28_freeze_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day28_freeze_hourly.cron.example)

## 2) Rule guardrail Day 28

Day 28 chỉ được `FREEZE_LOCKED_REPORT_FINALIZED` khi đồng thời PASS:
- Day 27 đã `VALIDATED_FOR_FREEZE`
- Freeze window đã bật
- Freeze window được quan sát đủ `>= 24h`
- Không có thay đổi critical trong cửa sổ freeze
- SLO ổn định trong 24h
- Không có incident Sev-1/Sev-2 trong 24h
- Báo cáo post-cutover đã sẵn sàng

## 3) Báo cáo Day 28

- Freeze report: [reports/DAY28_FREEZE_REPORT.json](reports/DAY28_FREEZE_REPORT.json)
- Watcher report: [reports/DAY28_WATCHER_RESULT.json](reports/DAY28_WATCHER_RESULT.json)
- Trend report (24h): [reports/DAY28_FREEZE_TREND_24H.json](reports/DAY28_FREEZE_TREND_24H.json)

Trend runner:
- [../../shared/platform/migration_templates/day28_freeze_trend.py](../../shared/platform/migration_templates/day28_freeze_trend.py)

## 4) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day28_freeze_guarded.sh
bash infrastructure/docker/migration-day4/scripts/run_day28_freeze_hourly.sh
```

## 5) Trạng thái hiện tại

Theo dữ liệu hiện tại expected là `BLOCKED` cho đến khi Day 27 đạt `VALIDATED_FOR_FREEZE` và đủ điều kiện freeze 24h.
