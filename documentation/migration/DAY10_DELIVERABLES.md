# Day 10 Deliverables - Guarded Canary 20% + Load/Backpressure Test

Ngày thực hiện: 2026-02-21
Phụ thuộc từ Day 8-9:
- [DAY8_DELIVERABLES.md](DAY8_DELIVERABLES.md)
- [DAY9_DELIVERABLES.md](DAY9_DELIVERABLES.md)

## 1) Guarded rollout lên 20%

Env mục tiêu Day 10:
- [../../infrastructure/docker/migration-day4/.env.day10.canary20.example](../../infrastructure/docker/migration-day4/.env.day10.canary20.example)

Runner guardrail:
- [../../shared/platform/migration_templates/day10_rollout_runner.py](../../shared/platform/migration_templates/day10_rollout_runner.py)
- [../../shared/platform/migration_templates/day10_rollout_watcher.py](../../shared/platform/migration_templates/day10_rollout_watcher.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day10_rollout_guarded.sh](../../infrastructure/docker/migration-day4/scripts/run_day10_rollout_guarded.sh)

Báo cáo Day 10:
- [reports/DAY10_ROLLOUT_REPORT.json](reports/DAY10_ROLLOUT_REPORT.json)
- [reports/DAY10_WATCHER_RESULT.json](reports/DAY10_WATCHER_RESULT.json)

## 2) Load test + backpressure test

Runner Day 10 có tích hợp mô phỏng load/backpressure và guardrail metrics:
- p95 latency
- p99 latency
- error rate
- queue depth

Kết quả lưu trong block `load_backpressure` của report Day 10.

## 3) Kết quả hiện tại (dựa trên dữ liệu thật)

- `summary.status`: `BLOCKED`
- Nguyên nhân: Day 9 vẫn `NO_GO`, nên rollout 20% chưa được áp dụng.
- `rollout.effective_percent`: giữ ở mức hiện tại (10%).
- `load_backpressure.overall_status`: `PASS` (đã có baseline kiểm thử cho bước tăng tải).

## 4) Acceptance Day 10
- [x] Có cơ chế tăng canary 20% với guardrail an toàn.
- [x] Có load/backpressure checks và report đi kèm.
- [ ] Rollout 20% được áp dụng thực tế (đang chờ Day 9 = GO).

Khi Day 9 chuyển `GO`, script Day 10 sẽ tự động:
- apply profile 20% vào file active: `infrastructure/docker/migration-day4/.env.day10.active`
- cập nhật checkbox Day 10 trong checklist migration.

## 5) Handoff Day 11
- Tiếp tục tích lũy trend Day 8/9 cho đến khi Day 9 chuyển `GO`.
- Re-run Day 10 rollout script để áp dụng 20%.
- Khi rollout thành công, chuyển sang tuning bottleneck (Day 11-12).

## 6) QA/Ops simulation (dev)

Script mô phỏng end-to-end khi Day 9 chuyển `GO`:
- [../../infrastructure/docker/migration-day4/scripts/simulate_day10_go_dev.sh](../../infrastructure/docker/migration-day4/scripts/simulate_day10_go_dev.sh)

Lệnh chạy:

```bash
bash infrastructure/docker/migration-day4/scripts/simulate_day10_go_dev.sh
```

Artifacts mô phỏng:
- `reports/DAY10_ROLLOUT_REPORT_SIMULATED_GO.json`
- `reports/DAY10_WATCHER_RESULT_SIMULATED_GO.json`

Lưu ý: script sẽ tự backup và restore state để không làm thay đổi trạng thái thật của Day 9/checklist/env active.
