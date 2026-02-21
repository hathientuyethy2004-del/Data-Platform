# Day 19 Deliverables - Guarded Read Switch 50%

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY18_DELIVERABLES.md](DAY18_DELIVERABLES.md)

## 1) Runner + watcher Day 19

Runner Day 19:
- [../../shared/platform/migration_templates/day19_read_switch_runner.py](../../shared/platform/migration_templates/day19_read_switch_runner.py)

Watcher checklist Day 18-19:
- [../../shared/platform/migration_templates/day19_read_switch_watcher.py](../../shared/platform/migration_templates/day19_read_switch_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day19_read_switch_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day19_read_switch_guarded.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day19_read_switch_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day19_read_switch_hourly.sh)

Env profile:
- [../../infrastructure/docker/migration-day4/.env.day19.read50.example](../../infrastructure/docker/migration-day4/.env.day19.read50.example)

Cron template:
- [../../infrastructure/docker/migration-day4/scripts/day19_read_switch_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day19_read_switch_hourly.cron.example)

## 2) Rule guardrail Day 19

Tăng read switch lên 50% chỉ được áp dụng khi đồng thời PASS:
- Day 18 đã `READ_SWITCHED_30`
- Day 15 write/load effective percent >= 50%
- Target read switch đúng 50%
- Stepwise increase an toàn từ 30% -> 50%
- Monitoring latency/error đạt ngưỡng

## 3) Báo cáo Day 19

- Read switch report: [reports/DAY19_READ_SWITCH_REPORT.json](reports/DAY19_READ_SWITCH_REPORT.json)
- Watcher report: [reports/DAY19_WATCHER_RESULT.json](reports/DAY19_WATCHER_RESULT.json)
- Trend report (24h): [reports/DAY19_READ_SWITCH_TREND_24H.json](reports/DAY19_READ_SWITCH_TREND_24H.json)

## 4) Trạng thái hiện tại

Theo dữ liệu hiện tại, Day 19 expected là `BLOCKED` vì Day 18 chưa đạt `READ_SWITCHED_30` và Day 15 chưa đạt 50% write/load.

## 5) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day19_read_switch_guarded.sh
bash infrastructure/docker/migration-day4/scripts/run_day19_read_switch_hourly.sh
```

## 6) Next step

Khi Day 18 chuyển `READ_SWITCHED_30` và điều kiện Day 15 đạt ngưỡng, re-run Day 19 để nâng read switch lên 50%.
