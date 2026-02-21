# Day 11 Deliverables - Bottleneck Tuning + Alert Threshold Optimization

Ngày thực hiện: 2026-02-21
Phụ thuộc từ Day 10:
- [DAY10_DELIVERABLES.md](DAY10_DELIVERABLES.md)

## 1) Khắc phục bottleneck (analysis + tuning plan)

Runner Day 11:
- [../../shared/platform/migration_templates/day11_tuning_runner.py](../../shared/platform/migration_templates/day11_tuning_runner.py)

Script vận hành:
- [../../infrastructure/docker/migration-day4/scripts/run_day11_tuning.sh](../../infrastructure/docker/migration-day4/scripts/run_day11_tuning.sh)

Kết quả phân tích bottleneck trong run hiện tại:
- `detected_items`: `[]` (không thấy điểm nghẽn gần ngưỡng ở baseline hiện tại)
- Đã sinh action plan cho: partition, batch size, retry, timeouts, connection pool.

## 2) Tune alert threshold giảm false positive

Tuned threshold policy:
- [../../infrastructure/docker/migration-day4/alert_thresholds.day11.tuned.json](../../infrastructure/docker/migration-day4/alert_thresholds.day11.tuned.json)

Điểm chính:
- `latency_p95_warning_ms=300`
- `latency_p99_critical_ms=700`
- `error_rate_warning_pct=0.625`
- `queue_depth_warning=171`
- `min_consecutive_breaches=3`
- `evaluation_window_minutes=10`
- `cooldown_minutes=15`

## 3) Báo cáo Day 11

- [reports/DAY11_TUNING_REPORT.json](reports/DAY11_TUNING_REPORT.json)

Kết quả run hiện tại:
- `summary.status`: `TUNED`
- `decision`: `Day 11 tuning ready for rollout`

## 4) Acceptance Day 11
- [x] Có cơ chế phân tích bottleneck theo data Day 10.
- [x] Có policy alert threshold tuned để giảm false positive.
- [x] Có report Day 11 và script vận hành đi kèm.

## 5) Handoff Day 12
- Áp dụng policy tuned vào dashboard/alert manager staging.
- Theo dõi false positive rate sau tuning và điều chỉnh nhỏ nếu cần.
- Chuẩn bị đầu vào cho Day 13 chaos test.
