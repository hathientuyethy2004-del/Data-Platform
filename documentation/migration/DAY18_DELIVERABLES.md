# Day 18 Deliverables - Guarded Read Switch 30%

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY17_DELIVERABLES.md](DAY17_DELIVERABLES.md)

## 1) Runner + watcher Day 18

Runner Day 18:
- [../../shared/platform/migration_templates/day18_read_switch_runner.py](../../shared/platform/migration_templates/day18_read_switch_runner.py)

Watcher checklist Day 18-19:
- [../../shared/platform/migration_templates/day18_read_switch_watcher.py](../../shared/platform/migration_templates/day18_read_switch_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day18_read_switch_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day18_read_switch_guarded.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day18_read_switch_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day18_read_switch_hourly.sh)
- [../../infrastructure/docker/migration-day4/scripts/day18_read_switch_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day18_read_switch_hourly.cron.example)

Env profile:
- [../../infrastructure/docker/migration-day4/.env.day18.read30.example](../../infrastructure/docker/migration-day4/.env.day18.read30.example)

## 2) Rule guardrail Day 18

Tăng read switch lên 30% chỉ được áp dụng khi đồng thời PASS:
- Day 17 đã `READ_SWITCHED_10`
- Day 15 write/load effective percent >= 50%
- Target read switch đúng 30%
- Stepwise increase an toàn từ 10% -> 30%
- Monitoring latency/error đạt ngưỡng

## 3) Báo cáo Day 18

- Read switch report: [reports/DAY18_READ_SWITCH_REPORT.json](reports/DAY18_READ_SWITCH_REPORT.json)
- Watcher report: [reports/DAY18_WATCHER_RESULT.json](reports/DAY18_WATCHER_RESULT.json)
- Read switch trend 24h: [reports/DAY18_READ_SWITCH_TREND_24H.json](reports/DAY18_READ_SWITCH_TREND_24H.json)
- History snapshots: `reports/history/DAY18_READ_SWITCH_REPORT_*.json`

Trend runner:
- [../../shared/platform/migration_templates/day18_read_switch_trend.py](../../shared/platform/migration_templates/day18_read_switch_trend.py)

## 4) Trạng thái hiện tại

Theo dữ liệu hiện tại, Day 18 expected là `BLOCKED` vì Day 17 chưa bật được read switch 10% và Day 15 chưa đạt 50% write/load.

## 5) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day18_read_switch_guarded.sh
```

## 6) Next step

Khi Day 17 chuyển `READ_SWITCHED_10` và điều kiện Day 15 đạt ngưỡng, re-run Day 18 để nâng read switch lên 30%.

Day 18 hourly automation:

```bash
bash infrastructure/docker/migration-day4/scripts/run_day18_read_switch_hourly.sh
```

Trend report sẽ tự ghi `last_transition_to_read_switched_30_at` khi phát hiện chuyển trạng thái `BLOCKED -> READ_SWITCHED_30`.
