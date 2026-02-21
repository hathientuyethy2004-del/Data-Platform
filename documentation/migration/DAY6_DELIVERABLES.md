# Day 6 Deliverables - Fix mismatch groups + regression tests + rollback runbook

Ngày thực hiện: 2026-02-21
Tham chiếu baseline Day 5:
- [reports/BASELINE_COMPARE_REPORT_DAY5.json](reports/BASELINE_COMPARE_REPORT_DAY5.json)

## 1) Sửa mismatch theo nhóm lỗi

Đã bổ sung module chuẩn hóa/so sánh để xử lý 4 nhóm mismatch phổ biến:
- **Schema mismatch**: thêm field thiếu theo `required_fields` + `defaults`
- **Timezone mismatch**: chuẩn hóa timestamp về UTC ISO-8601
- **Rounding mismatch**: chuẩn hóa số với scale thống nhất
- **Null semantics mismatch**: map `""`, `"null"`, `"n/a"`, ... về `None`

Code:
- [../../shared/platform/migration_templates/compare_utils.py](../../shared/platform/migration_templates/compare_utils.py)

## 2) Regression tests đã thêm

Test hồi quy cho các nhóm mismatch:
- [../../shared/tests/test_migration_compare_utils.py](../../shared/tests/test_migration_compare_utils.py)
- [reports/DAY6_REGRESSION_RESULT.json](reports/DAY6_REGRESSION_RESULT.json)

Bao phủ:
- normalize null-like values
- normalize timestamp về UTC
- normalize numeric rounding
- compare record end-to-end qua schema/timezone/rounding/null semantics

## 3) Cập nhật rollback runbook

Runbook rollback đã bổ sung trigger, thao tác, và tiêu chí thoát rollback mode:
- [ROLLBACK_RUNBOOK.md](ROLLBACK_RUNBOOK.md)

## 4) Acceptance Day 6
- [x] Có bản vá mismatch theo 4 nhóm lỗi chuẩn.
- [x] Có regression tests cho mismatch đã fix.
- [x] Có rollback runbook cập nhật để vận hành sự cố migration.

## 5) Handoff Day 7 (Gate 1)
- Chạy regression tests + smoke Day 5.
- Theo dõi dual-run staging >= 24h.
- Xác nhận không có mismatch critical trước khi qua tuần 2.
