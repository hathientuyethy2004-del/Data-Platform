# Rollback Runbook (Migration Week 1-2)

Mục tiêu: rollback nhanh, an toàn, không mất dữ liệu khi dual-run/canary có vấn đề.

## 1) Trigger rollback
- Error rate > 1.5% trong 10 phút liên tiếp.
- p99 latency > 2500ms trong 15 phút liên tiếp.
- Mismatch critical trong compare report vượt ngưỡng (schema break / PK mismatch vượt ngưỡng).

## 2) Quyền quyết định
- Incident Commander: Tech Lead
- Approver: Platform/DevOps backup

## 3) RTO/RPO mục tiêu
- RTO: <= 15 phút
- RPO: <= 5 phút cho path serving, <= 1 batch window cho path processing

## 4) Thao tác rollback chuẩn
1. Freeze deploy mới.
2. Tắt read từ OSS:
   - `READ_FROM_OSS_SERVING=false`
3. Tắt OSS write path (nếu cần):
   - `USE_OSS_INGESTION=false`
   - `USE_OSS_QUALITY=false`
   - `USE_OSS_SERVING=false`
4. Giữ dual-run compare tùy severity:
   - Critical: `DUAL_RUN_ENABLED=false`
   - Non-critical: giữ `DUAL_RUN_ENABLED=true` để tiếp tục thu dữ liệu điều tra.
5. Redeploy/restart service với env mới.
6. Verify:
   - API health, error rate, p99
   - Queue lag và batch completion
   - Compare report trạng thái ổn định

## 5) Checklist sau rollback
- [ ] Incident timeline đã ghi log.
- [ ] Snapshot cấu hình trước/sau rollback đã lưu.
- [ ] Mismatch root-cause ticket đã tạo.
- [ ] Regression test cho bug đã thêm vào backlog Day 6.

## 6) Mẫu env rollback nhanh
```bash
export READ_FROM_OSS_SERVING=false
export USE_OSS_INGESTION=false
export USE_OSS_QUALITY=false
export USE_OSS_SERVING=false
export DUAL_RUN_ENABLED=false
export DUAL_RUN_COMPARE_ENABLED=true
```

## 7) Exit rollback mode
Chỉ mở lại canary khi thỏa cả 3 điều kiện:
- Không còn critical issue trong compare report >= 24h.
- Error rate và latency về dưới ngưỡng KPI Day 1.
- Regression tests pass 100% cho nhóm lỗi vừa sửa.
