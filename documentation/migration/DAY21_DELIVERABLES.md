# Day 21 Deliverables - Gate 3 Guarded + Watcher

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY20_DELIVERABLES.md](DAY20_DELIVERABLES.md)

## 1) Runner + watcher Day 21

Runner Gate 3 Day 21:
- [../../shared/platform/migration_templates/day21_gate3_runner.py](../../shared/platform/migration_templates/day21_gate3_runner.py)

Watcher checklist Day 21:
- [../../shared/platform/migration_templates/day21_gate3_watcher.py](../../shared/platform/migration_templates/day21_gate3_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day21_gate3_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day21_gate3_guarded.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day21_gate3_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day21_gate3_hourly.sh)

Cron template:
- [../../infrastructure/docker/migration-day4/scripts/day21_gate3_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day21_gate3_hourly.cron.example)

## 2) Rule guardrail Day 21 (Gate 3)

Gate 3 chỉ PASS khi đồng thời thỏa:
- 80% traffic ổn định >= 72h
- Compare pass rate >= 99.5%

Khi Gate 3 PASS:
- Duyệt full cutover tuần 4

## 3) Báo cáo Day 21

- Gate 3 report: [reports/DAY21_GATE3_REPORT.json](reports/DAY21_GATE3_REPORT.json)
- Watcher report: [reports/DAY21_WATCHER_RESULT.json](reports/DAY21_WATCHER_RESULT.json)
- Trend report (24h): [reports/DAY21_GATE3_TREND_24H.json](reports/DAY21_GATE3_TREND_24H.json)

Trend runner:
- [../../shared/platform/migration_templates/day21_gate3_trend.py](../../shared/platform/migration_templates/day21_gate3_trend.py)

## 4) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day21_gate3_guarded.sh
bash infrastructure/docker/migration-day4/scripts/run_day21_gate3_hourly.sh
```

## 5) Trạng thái hiện tại

Theo dữ liệu hiện tại expected là `NO_GO` khi điều kiện Day 20 chưa đạt `TRAFFIC_80_APPLIED` và chưa đủ cửa sổ ổn định 72h.
