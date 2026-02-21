# Day 25-26 Deliverables - Guarded Read Cutover 100% + Legacy Draining

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY22_24_DELIVERABLES.md](DAY22_24_DELIVERABLES.md)

## 1) Runner + watcher Day 25-26

Runner Day 25-26:
- [../../shared/platform/migration_templates/day25_26_read_cutover_runner.py](../../shared/platform/migration_templates/day25_26_read_cutover_runner.py)

Watcher checklist Day 25-26:
- [../../shared/platform/migration_templates/day25_26_read_cutover_watcher.py](../../shared/platform/migration_templates/day25_26_read_cutover_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day25_26_read_cutover_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day25_26_read_cutover_guarded.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day25_26_read_cutover_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day25_26_read_cutover_hourly.sh)

Env profile:
- [../../infrastructure/docker/migration-day4/.env.day25_26.read100.example](../../infrastructure/docker/migration-day4/.env.day25_26.read100.example)

Cron template:
- [../../infrastructure/docker/migration-day4/scripts/day25_26_read_cutover_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day25_26_read_cutover_hourly.cron.example)

## 2) Rule guardrail Day 25-26

Cutover read path 100% chỉ được áp dụng khi đồng thời PASS:
- Day 22-24 đã `WRITE_LOAD_100_SHADOW_READ`
- Day 21 Gate 3 đã `PASS`
- Target read switch đúng 100%
- Stepwise increase an toàn từ 50% -> 100%
- Legacy draining tối thiểu: jobs/routes/configs đã vô hiệu hóa hoặc lưu trữ
- Monitoring latency/error đạt ngưỡng

## 3) Báo cáo Day 25-26

- Read cutover report: [reports/DAY25_26_READ_CUTOVER_REPORT.json](reports/DAY25_26_READ_CUTOVER_REPORT.json)
- Watcher report: [reports/DAY25_26_WATCHER_RESULT.json](reports/DAY25_26_WATCHER_RESULT.json)
- Trend report (24h): [reports/DAY25_26_READ_CUTOVER_TREND_24H.json](reports/DAY25_26_READ_CUTOVER_TREND_24H.json)

Trend runner:
- [../../shared/platform/migration_templates/day25_26_read_cutover_trend.py](../../shared/platform/migration_templates/day25_26_read_cutover_trend.py)

## 4) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day25_26_read_cutover_guarded.sh
bash infrastructure/docker/migration-day4/scripts/run_day25_26_read_cutover_hourly.sh
```

## 5) Trạng thái hiện tại

Theo dữ liệu hiện tại expected là `BLOCKED` cho đến khi Day 22-24 đạt `WRITE_LOAD_100_SHADOW_READ`.
