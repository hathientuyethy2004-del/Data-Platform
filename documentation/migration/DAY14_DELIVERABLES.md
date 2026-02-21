# Day 14 Deliverables - Gate 2 Evaluation (Week 2)

Ngày thực hiện: 2026-02-21
Phụ thuộc từ Day 10-13:
- [DAY10_DELIVERABLES.md](DAY10_DELIVERABLES.md)
- [DAY11_DELIVERABLES.md](DAY11_DELIVERABLES.md)
- [DAY12_DELIVERABLES.md](DAY12_DELIVERABLES.md)
- [DAY13_DELIVERABLES.md](DAY13_DELIVERABLES.md)

## 1) Runner Gate 2

Runner Day 14:
- [../../shared/platform/migration_templates/day14_gate2_runner.py](../../shared/platform/migration_templates/day14_gate2_runner.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day14_gate2.sh](../../infrastructure/docker/migration-day4/scripts/run_day14_gate2.sh)
- [../../infrastructure/docker/migration-day4/scripts/run_day14_gate2_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day14_gate2_hourly.sh)
- [../../infrastructure/docker/migration-day4/scripts/day14_gate2_hourly.cron.example](../../infrastructure/docker/migration-day4/scripts/day14_gate2_hourly.cron.example)

Incident log input:
- [reports/DAY14_INCIDENT_LOG.json](reports/DAY14_INCIDENT_LOG.json)

Watcher đồng bộ checklist:
- [../../shared/platform/migration_templates/day14_gate2_watcher.py](../../shared/platform/migration_templates/day14_gate2_watcher.py)

## 2) Báo cáo Gate 2

- [reports/DAY14_GATE2_REPORT.json](reports/DAY14_GATE2_REPORT.json)

Kết quả hiện tại:
- `summary.status`: `NO_GO`
- `approve_scale_week3`: `false`
- Blocker chính: `canary_20_stable_48h` (mới ~0.19h / yêu cầu 48h)

## 3) Trạng thái các tiêu chí Gate 2

- `20% canary ổn định >= 48h`: `FAIL`
- `Không có incident Sev-1/Sev-2`: `PASS`
- `Resilience/data integrity từ Day 13`: `PASS`

## 4) Acceptance Day 14
- [x] Có runner Gate 2 và script vận hành.
- [x] Có report Gate 2 với blocker/ETA rõ ràng.
- [ ] Được duyệt tăng tỷ lệ tuần 3 (đang chờ đủ cửa sổ ổn định 48h).

## 5) Handoff Week 3
- Duy trì 20% canary cho đủ 48h ổn định.
- Re-run Gate 2 khi đạt ngưỡng thời gian.
- Nếu report chuyển `PASS`, bắt đầu kế hoạch Day 15-16.
