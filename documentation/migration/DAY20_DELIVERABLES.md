# Day 20 Deliverables - Guarded Traffic 80%

Ngày thực hiện: 2026-02-21
Phụ thuộc: [DAY19_DELIVERABLES.md](DAY19_DELIVERABLES.md)

## 1) Runner + watcher Day 20

Runner Day 20:
- [../../shared/platform/migration_templates/day20_traffic_runner.py](../../shared/platform/migration_templates/day20_traffic_runner.py)

Watcher checklist Day 20:
- [../../shared/platform/migration_templates/day20_traffic_watcher.py](../../shared/platform/migration_templates/day20_traffic_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day20_traffic_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day20_traffic_guarded.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day20_traffic_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day20_traffic_hourly.sh)

Env profile:
- [../../infrastructure/docker/migration-day4/.env.day20.traffic80.example](../../infrastructure/docker/migration-day4/.env.day20.traffic80.example)

Cron template:
- [../../infrastructure/docker/migration-day4/scripts/day20_traffic_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day20_traffic_hourly.cron.example)

## 2) Rule guardrail Day 20

Tăng tổng traffic lên 80% chỉ được áp dụng khi đồng thời PASS:
- Day 19 đã `READ_SWITCHED_50`
- Day 15 write/load effective percent >= 50%
- Target tổng traffic đúng 80%
- Stepwise increase an toàn từ 50% -> 80%
- Audit permission + secret rotation + rate limiting đều PASS
- Monitoring latency/error đạt ngưỡng

## 3) Báo cáo Day 20

- Traffic report: [reports/DAY20_TRAFFIC_REPORT.json](reports/DAY20_TRAFFIC_REPORT.json)
- Watcher report: [reports/DAY20_WATCHER_RESULT.json](reports/DAY20_WATCHER_RESULT.json)
- Trend report (24h): [reports/DAY20_TRAFFIC_TREND_24H.json](reports/DAY20_TRAFFIC_TREND_24H.json)

Trend runner:
- [../../shared/platform/migration_templates/day20_traffic_trend.py](../../shared/platform/migration_templates/day20_traffic_trend.py)

## 4) Trạng thái hiện tại

Theo dữ liệu hiện tại, Day 20 expected là `BLOCKED` khi Day 19 chưa đạt `READ_SWITCHED_50`.

## 5) Lệnh chạy

```bash
bash infrastructure/docker/migration-day4/scripts/run_day20_traffic_guarded.sh
bash infrastructure/docker/migration-day4/scripts/run_day20_traffic_hourly.sh
```

## 6) Next step

Khi Day 19 chuyển `READ_SWITCHED_50`, re-run Day 20 để nâng tổng traffic lên 80%.
