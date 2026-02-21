# Day 17 Deliverables - Guarded Read Switch 10%

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY16_DELIVERABLES.md](DAY16_DELIVERABLES.md)

## 1) Runner + watcher Day 17

Runner Day 17:
- [../../shared/platform/migration_templates/day17_read_switch_runner.py](../../shared/platform/migration_templates/day17_read_switch_runner.py)

Watcher checklist Day 17:
- [../../shared/platform/migration_templates/day17_read_switch_watcher.py](../../shared/platform/migration_templates/day17_read_switch_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day17_read_switch_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day17_read_switch_guarded.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day17_read_switch_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day17_read_switch_hourly.sh)
- [../../infrastructure/docker/migration-day4/scripts/day17_read_switch_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day17_read_switch_hourly.cron.example)

Env profile:
- [../../infrastructure/docker/migration-day4/.env.day17.read10.example](../../infrastructure/docker/migration-day4/.env.day17.read10.example)

## 2) Rule guardrail Day 17

Read switch 10% chỉ được áp dụng khi đồng thời PASS:
- Day 16 `READY_FOR_DAY17`
- Day 15 write/load effective percent >= 50%
- Target read switch đúng 10%
- Monitoring latency/error đạt ngưỡng

## 3) Báo cáo Day 17

- Read switch report: [reports/DAY17_READ_SWITCH_REPORT.json](reports/DAY17_READ_SWITCH_REPORT.json)
- Watcher report: [reports/DAY17_WATCHER_RESULT.json](reports/DAY17_WATCHER_RESULT.json)
- Read switch trend 24h: [reports/DAY17_READ_SWITCH_TREND_24H.json](reports/DAY17_READ_SWITCH_TREND_24H.json)
- History snapshots: `reports/history/DAY17_READ_SWITCH_REPORT_*.json`

Trend runner:
- [../../shared/platform/migration_templates/day17_read_switch_trend.py](../../shared/platform/migration_templates/day17_read_switch_trend.py)

## 4) Trạng thái hiện tại

Theo dữ liệu hiện tại, Day 17 expected là `BLOCKED` do Day 16 vẫn `HOLD` và Day 15 chưa đạt 50% write/load.

## 5) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day17_read_switch_guarded.sh
```

## 6) Next step

Khi Day 16 chuyển `READY_FOR_DAY17`, re-run Day 17 để mở read switch 10% và bắt đầu tăng dần ở Day 18-19.

Day 17 hourly automation:

```bash
bash infrastructure/docker/migration-day4/scripts/run_day17_read_switch_hourly.sh
```

Trend report sẽ tự ghi `last_transition_to_read_switched_10_at` khi phát hiện chuyển trạng thái `BLOCKED -> READ_SWITCHED_10`.
