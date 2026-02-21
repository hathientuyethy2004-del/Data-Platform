# Day 16 Deliverables - Observation Readiness for Day 17

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY15_DELIVERABLES.md](DAY15_DELIVERABLES.md)

## 1) Runner Day 16

Runner đánh giá readiness Day 17:
- [../../shared/platform/migration_templates/day16_observation_runner.py](../../shared/platform/migration_templates/day16_observation_runner.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day16_observation.sh](../../infrastructure/docker/migration-day4/scripts/run_day16_observation.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day16_observation_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day16_observation_hourly.sh)
- [../../infrastructure/docker/migration-day4/scripts/day16_observation_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day16_observation_hourly.cron.example)

## 2) Tiêu chí đánh giá Day 16

- Day 15 đã scale lên 50% thành công (`SCALED_TO_50`, `effective_percent >= 50`)
- Day 15 compare trend ổn định (default: `total_runs >= 6`, `compare_pass_rate_pct >= 99%`, status `PASS`)
- Cron health cho Day 14/15 đang `PASS`

## 3) Báo cáo Day 16

- Observation report: [reports/DAY16_OBSERVATION_REPORT.json](reports/DAY16_OBSERVATION_REPORT.json)
- Observation trend 24h: [reports/DAY16_OBSERVATION_TREND_24H.json](reports/DAY16_OBSERVATION_TREND_24H.json)
- Watcher report: [reports/DAY16_WATCHER_RESULT.json](reports/DAY16_WATCHER_RESULT.json)
- History snapshots: `reports/history/DAY16_OBSERVATION_REPORT_*.json`
- Transition state: `reports/history/DAY16_OBSERVATION_STATE.json`
- Transition audit log: `reports/history/DAY16_OBSERVATION_TRANSITIONS.jsonl`

## 4) Trạng thái hiện tại

Theo dữ liệu hiện có, Day 16 expected là `HOLD` vì Day 15 chưa scale được 50% do Gate 2 vẫn `NO_GO`.

## 5) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day16_observation.sh
```

## 6) Next step

Khi Day 14 Gate 2 chuyển `PASS` và Day 15 scale thành công, re-run Day 16 để mở khóa Day 17 read-switch.

Day 16 hourly automation:

```bash
bash infrastructure/docker/migration-day4/scripts/run_day16_observation_hourly.sh
```

Script hourly sẽ tự ghi history/trend và transition `HOLD -> READY_FOR_DAY17` khi đủ điều kiện.
