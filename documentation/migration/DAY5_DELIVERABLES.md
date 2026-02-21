# Day 5 Deliverables - Smoke E2E OSS Path + Dual-run (0% read OSS) + Baseline Report

Ngày thực hiện: 2026-02-21
Phụ thuộc từ Day 1-4:
- [DAY1_DELIVERABLES.md](DAY1_DELIVERABLES.md)
- [DAY2_DELIVERABLES.md](DAY2_DELIVERABLES.md)
- [DAY3_DELIVERABLES.md](DAY3_DELIVERABLES.md)
- [DAY4_DELIVERABLES.md](DAY4_DELIVERABLES.md)

## 1) Smoke test end-to-end path OSS với dữ liệu mẫu

Script smoke E2E:
- [../../infrastructure/docker/migration-day4/scripts/run_day5_smoke_e2e.sh](../../infrastructure/docker/migration-day4/scripts/run_day5_smoke_e2e.sh)

Runner dùng router/adapters Day 3:
- [../../shared/platform/migration_templates/day5_smoke_runner.py](../../shared/platform/migration_templates/day5_smoke_runner.py)

Kết quả chạy ngày 2026-02-21:
- Status: `PASS`
- Artifact: [reports/DAY5_SMOKE_RESULT.json](reports/DAY5_SMOKE_RESULT.json)

## 2) Bật dual-run ở staging (0% traffic read từ OSS)

Profile env Day 5:
- [../../infrastructure/docker/migration-day4/.env.day5.dualrun.example](../../infrastructure/docker/migration-day4/.env.day5.dualrun.example)

Cấu hình xác nhận:
- `DUAL_RUN_ENABLED=true`
- `DUAL_RUN_COMPARE_ENABLED=true`
- `READ_FROM_OSS_SERVING=false`
- `USE_OSS_*` giữ `false` để read path vẫn legacy

## 3) Lưu kết quả compare đầu tiên + baseline report

Baseline compare report đã sinh:
- [reports/BASELINE_COMPARE_REPORT_DAY5.json](reports/BASELINE_COMPARE_REPORT_DAY5.json)

Template chuẩn compare report:
- [../../shared/platform/migration_templates/compare_report_template.json](../../shared/platform/migration_templates/compare_report_template.json)

## 4) Acceptance Day 5
- [x] Smoke E2E chạy pass với dữ liệu mẫu.
- [x] Dual-run bật, read path vẫn legacy (0% read OSS).
- [x] Có baseline compare report đầu tiên lưu tại thư mục reports.

## 5) Handoff Day 6
- Phân tích mismatch từ baseline report (nếu có).
- Sửa các nhóm lỗi schema/timezone/rounding/null semantics.
- Bổ sung regression tests cho các mismatch đã fix.
