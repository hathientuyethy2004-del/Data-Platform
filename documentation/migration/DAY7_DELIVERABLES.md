# Day 7 Deliverables - Gate 1 Evaluation (Week 1)

Ngày thực hiện: 2026-02-21
Phụ thuộc từ Day 5-6:
- [DAY5_DELIVERABLES.md](DAY5_DELIVERABLES.md)
- [DAY6_DELIVERABLES.md](DAY6_DELIVERABLES.md)

## 1) Tự động hóa kiểm Gate 1

Đã bổ sung script đánh giá Gate 1:
- [../../shared/platform/migration_templates/day7_gate_runner.py](../../shared/platform/migration_templates/day7_gate_runner.py)

Tiêu chí kiểm:
- Dual-run staging ổn định >= 24h.
- Không có mismatch critical.
- Smoke/baseline/regression prerequisite ở trạng thái pass.

## 2) Kết quả Gate 1 hiện tại

Báo cáo Day 7:
- [reports/DAY7_GATE1_REPORT.json](reports/DAY7_GATE1_REPORT.json)

Trạng thái chạy hiện tại:
- `status`: `FAIL`
- `allow_move_to_week2`: `false`
- Nguyên nhân chính: chưa đủ cửa sổ ổn định 24h (`observed_hours` < 24)
- Report có thêm ETA vận hành: `remaining_hours_to_gate` và `estimated_pass_at_utc`.

## 3) Những gì đã đạt trong Day 7

- [x] Có cơ chế evaluate Gate 1 tự động từ artifacts Day 5-6.
- [x] Điều kiện mismatch critical đang đạt (0 critical).
- [x] Có report quyết định gate ở định dạng JSON để audit.

## 4) Điều kiện còn thiếu để qua Gate 1

- [ ] Tiếp tục dual-run đến khi đạt >= 24h ổn định.
- [ ] Re-run Gate 1 và xác nhận `status=PASS`.
- [ ] Khi PASS thì mới check "Cho phép sang tuần 2" trong checklist.

## 5) Lệnh chạy Gate 1

```bash
PYTHONPATH=. python -m shared.platform.migration_templates.day7_gate_runner
```

## 6) Bước tiếp theo đã triển khai: auto-run theo giờ

Script wrapper hourly:
- [../../infrastructure/docker/migration-day4/scripts/run_day7_gate_hourly.sh](../../infrastructure/docker/migration-day4/scripts/run_day7_gate_hourly.sh)

Watcher tự check checklist Day 7:
- [../../shared/platform/migration_templates/day7_gate_watcher.py](../../shared/platform/migration_templates/day7_gate_watcher.py)

Cron template:
- [../../infrastructure/docker/migration-day4/scripts/day7_gate1.cron.example](../../infrastructure/docker/migration-day4/scripts/day7_gate1.cron.example)

Hành vi:
- Mỗi lần chạy sẽ cập nhật report latest: `reports/DAY7_GATE1_REPORT.json`
- Đồng thời lưu snapshot history theo timestamp trong `reports/history/`
- Tự động đồng bộ checkbox Day 7 trong checklist theo trạng thái gate mới nhất.
- Khi vừa chuyển từ `FAIL` sang `PASS`, watcher tự ghi `audit.gate_passed_timestamp` vào gate report.
- Log transition phục vụ audit được append tại `reports/history/DAY7_GATE1_TRANSITIONS.jsonl`.
- Khi vừa chuyển từ `FAIL` sang `PASS`, watcher tự sinh file closure: `DAY7_GATE1_CLOSURE.md` để chốt audit/handoff sang Tuần 2.
- Script không fail hard khi gate chưa pass (phù hợp giai đoạn chưa đủ 24h)

Lệnh chạy nhanh:

```bash
bash infrastructure/docker/migration-day4/scripts/run_day7_gate_hourly.sh
```
