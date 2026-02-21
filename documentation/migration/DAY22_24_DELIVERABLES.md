# Day 22-24 Deliverables - Guarded Batch Cutover 100% Write/Load + Shadow Read

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY21_DELIVERABLES.md](DAY21_DELIVERABLES.md)

## 1) Runner + watcher Day 22-24

Runner Day 22-24:
- [../../shared/platform/migration_templates/day22_24_cutover_runner.py](../../shared/platform/migration_templates/day22_24_cutover_runner.py)

Watcher checklist Day 22-24:
- [../../shared/platform/migration_templates/day22_24_cutover_watcher.py](../../shared/platform/migration_templates/day22_24_cutover_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day22_24_cutover_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day22_24_cutover_guarded.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day22_24_cutover_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day22_24_cutover_hourly.sh)

Env profile:
- [../../infrastructure/docker/migration-day4/.env.day22_24.cutover100.example](../../infrastructure/docker/migration-day4/.env.day22_24.cutover100.example)

Cron template:
- [../../infrastructure/docker/migration-day4/scripts/day22_24_cutover_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day22_24_cutover_hourly.cron.example)

## 2) Rule guardrail Day 22-24

Batch cutover chỉ được áp dụng khi đồng thời PASS:
- Day 21 Gate 3 đã `PASS` (approve full cutover tuần 4)
- Day 20 baseline traffic đạt >= 80%
- Target write/load đúng 100%
- Stepwise tăng an toàn từ 80% -> 100%
- Shadow read từ legacy bật và cửa sổ giữ trong 2-3 ngày
- Monitoring latency/error đạt ngưỡng

## 3) Báo cáo Day 22-24

- Cutover report: [reports/DAY22_24_CUTOVER_REPORT.json](reports/DAY22_24_CUTOVER_REPORT.json)
- Watcher report: [reports/DAY22_24_WATCHER_RESULT.json](reports/DAY22_24_WATCHER_RESULT.json)
- Trend report (24h): [reports/DAY22_24_CUTOVER_TREND_24H.json](reports/DAY22_24_CUTOVER_TREND_24H.json)

Trend runner:
- [../../shared/platform/migration_templates/day22_24_cutover_trend.py](../../shared/platform/migration_templates/day22_24_cutover_trend.py)

## 4) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day22_24_cutover_guarded.sh
bash infrastructure/docker/migration-day4/scripts/run_day22_24_cutover_hourly.sh
```

## 5) Trạng thái hiện tại

Theo dữ liệu hiện tại expected là `BLOCKED` cho đến khi Day 21 Gate 3 chuyển `PASS`.
