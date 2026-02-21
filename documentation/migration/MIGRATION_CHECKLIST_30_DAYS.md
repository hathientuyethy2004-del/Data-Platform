# Checklist Migration 30 Ngày (Code cũ -> Open Source Stack)

## Mục tiêu
- Chuyển đổi an toàn theo mô hình **strangler pattern**.
- Không downtime production.
- Có khả năng rollback trong vòng <= 15 phút.
- Đảm bảo chất lượng dữ liệu và SLA trước khi cutover 100%.

## Scope kỹ thuật (đề xuất team 3-6 người)
- Ingestion: Kafka/Kafka Connect (hoặc worker Python làm bridge ban đầu)
- Orchestration: Airflow
- Processing: Spark
- Serving: FastAPI + Redis
- Quality: Great Expectations
- Observability: Prometheus + Grafana + Loki

---

## Tuần 1 (Ngày 1-7): Baseline + Contracts + Dual-Run Ready

### Ngày 1
- [x] Chốt scope migration: dịch vụ, pipeline, bảng dữ liệu, endpoint cần thay.
- [x] Chốt KPI migration: latency, throughput, quality pass rate, error budget.
- [x] Chốt owner theo hạng mục (Ingestion/Processing/Serving/QA/Ops).

**Deliverables Ngày 1**: xem [DAY1_DELIVERABLES.md](DAY1_DELIVERABLES.md)

### Ngày 2
- [x] Tạo danh sách data contracts (schema event + schema bảng output).
- [x] Định nghĩa rule so sánh kết quả (row count, checksum, null rate, duplicate rate).
- [x] Chốt format output chuẩn để so sánh (JSON/Parquet table compare).

**Deliverables Ngày 2**: xem [DAY2_DELIVERABLES.md](DAY2_DELIVERABLES.md)

### Ngày 3
- [x] Tạo feature flags migration (`USE_OSS_*`, `DUAL_RUN_*`, `READ_FROM_OSS_*`).
- [x] Tách interface/ports và adapter cho code cũ + code mới.
- [x] Thêm logging marker cho mỗi path (legacy/oss/dual-run).

**Deliverables Ngày 3**: xem [DAY3_DELIVERABLES.md](DAY3_DELIVERABLES.md)

### Ngày 4
- [x] Dựng môi trường OSS tối thiểu (dev/staging): Kafka, Airflow, Redis, Prometheus.
- [x] Kết nối storage và cấu hình credentials/secret manager.
- [x] Verify healthcheck toàn bộ service.

**Deliverables Ngày 4**: xem [DAY4_DELIVERABLES.md](DAY4_DELIVERABLES.md)

### Ngày 5
- [x] Chạy smoke test end-to-end path OSS với dữ liệu mẫu.
- [x] Bật dual-run ở staging (0% traffic read từ OSS).
- [x] Lưu kết quả compare đầu tiên + baseline report.

**Deliverables Ngày 5**: xem [DAY5_DELIVERABLES.md](DAY5_DELIVERABLES.md)

### Ngày 6
- [x] Sửa mismatch theo nhóm lỗi: schema, timezone, rounding, null semantics.
- [x] Thêm test hồi quy cho mismatch đã gặp.
- [x] Cập nhật runbook rollback.

**Deliverables Ngày 6**: xem [DAY6_DELIVERABLES.md](DAY6_DELIVERABLES.md)

### Ngày 7 (Gate 1)
- [ ] Gate tuần 1: dual-run staging ổn định >= 24h.
- [x] Không có mismatch critical.
- [x] Thiết lập auto-run Gate 1 theo giờ (latest + history report).
- [ ] Cho phép sang tuần 2.

**Deliverables Ngày 7**: xem [DAY7_DELIVERABLES.md](DAY7_DELIVERABLES.md)

> Ghi chú: các checkbox Gate 1 của Ngày 7 được đồng bộ tự động từ `DAY7_GATE1_REPORT.json` bởi watcher.

---

## Tuần 2 (Ngày 8-14): Canary 10-20% + Stabilization

### Ngày 8-9
- [x] Bật canary 10% write/load vào path OSS.
- [x] Vẫn giữ read path từ legacy.
- [x] Theo dõi dashboard SLO + chất lượng dữ liệu.

**Deliverables Ngày 8**: xem [DAY8_DELIVERABLES.md](DAY8_DELIVERABLES.md)

**Deliverables Ngày 9**: xem [DAY9_DELIVERABLES.md](DAY9_DELIVERABLES.md)

> Ghi chú vận hành Day 8: theo dõi liên tục qua `DAY8_CANARY_STATUS.json`, history hourly và `DAY8_CANARY_TREND_24H.json`.
> Ghi chú Day 9: quyết định GO/NO_GO cho Day 10 được theo dõi qua `DAY9_STABILITY_REPORT.json`.

### Ngày 10
- [ ] Tăng canary lên 20% nếu error rate và mismatch trong ngưỡng.
- [x] Chạy load test peak hour + backpressure test.

**Deliverables Ngày 10**: xem [DAY10_DELIVERABLES.md](DAY10_DELIVERABLES.md)

> Ghi chú Day 10: rollout 20% đang bị guardrail chặn vì Day 9 hiện `NO_GO`; giữ mức 10% cho đến khi blockers được xử lý.
> Ghi chú đồng bộ: checkbox "Tăng canary lên 20%" được watcher Day 10 tự cập nhật từ `DAY10_ROLLOUT_REPORT.json`.

### Ngày 11-12
- [x] Khắc phục bottleneck (partition, batch size, retry, timeouts, connection pool).
- [x] Tune alert threshold tránh false positive.

**Deliverables Ngày 11**: xem [DAY11_DELIVERABLES.md](DAY11_DELIVERABLES.md)
**Deliverables Ngày 12**: xem [DAY12_DELIVERABLES.md](DAY12_DELIVERABLES.md)

### Ngày 13
- [x] Chaos test nhẹ: restart service, ngắt kết nối ngắn, validate retry/idempotency.
- [x] Verify recovery time và data integrity.

**Deliverables Ngày 13**: xem [DAY13_DELIVERABLES.md](DAY13_DELIVERABLES.md)

### Ngày 14 (Gate 2)
- [ ] Gate tuần 2: 20% canary ổn định >= 48h.
- [x] Không có incident Sev-1/Sev-2.
- [ ] Duyệt tăng tỷ lệ tuần 3.

**Deliverables Ngày 14**: xem [DAY14_DELIVERABLES.md](DAY14_DELIVERABLES.md)

> Ghi chú Day 14: Gate 2 hiện `NO_GO` do chưa đủ cửa sổ ổn định 48h ở mức 20%; re-run sau khi đủ thời gian.
> Re-check theo giờ: `bash infrastructure/docker/migration-day4/scripts/run_day14_gate2_hourly.sh`

---

## Tuần 3 (Ngày 15-21): Scale 50-80% + Read Switch có kiểm soát

### Ngày 15-16
- [ ] Tăng tỷ lệ write/load OSS lên 50%.
- [x] Giữ dual-run compare tự động mỗi giờ.

**Deliverables Ngày 15**: xem [DAY15_DELIVERABLES.md](DAY15_DELIVERABLES.md)
**Deliverables Ngày 16**: xem [DAY16_DELIVERABLES.md](DAY16_DELIVERABLES.md)

> Ghi chú Day 15: scale-up 50% bị guardrail chặn cho đến khi Day 14 Gate 2 chuyển `PASS`.
> Hourly compare snapshot/trend: `bash infrastructure/docker/migration-day4/scripts/run_day15_compare_hourly.sh`
> Day 16 observation readiness: `bash infrastructure/docker/migration-day4/scripts/run_day16_observation.sh`
> Day 16 hourly observation + auto transition audit: `bash infrastructure/docker/migration-day4/scripts/run_day16_observation_hourly.sh`

### Ngày 17
- [ ] Bật read switch 10% sang OSS cho endpoint/pipeline đã ổn định.
- [ ] Theo dõi latency p95/p99 và error rate.

**Deliverables Ngày 17**: xem [DAY17_DELIVERABLES.md](DAY17_DELIVERABLES.md)

> Ghi chú Day 17: read switch 10% được guardrail chặn cho đến khi Day 16 `READY_FOR_DAY17`.
> Run Day 17 guarded: `bash infrastructure/docker/migration-day4/scripts/run_day17_read_switch_guarded.sh`
> Day 17 hourly snapshot/trend: `bash infrastructure/docker/migration-day4/scripts/run_day17_read_switch_hourly.sh`

### Ngày 18-19
- [ ] Tăng read switch 30% rồi 50% nếu đạt SLO.
- [ ] Validate freshness và tính đúng business metrics.

**Deliverables Ngày 18**: xem [DAY18_DELIVERABLES.md](DAY18_DELIVERABLES.md)
**Deliverables Ngày 19**: xem [DAY19_DELIVERABLES.md](DAY19_DELIVERABLES.md)

> Ghi chú Day 18: read switch 30% được guardrail chặn cho đến khi Day 17 `READ_SWITCHED_10`.
> Run Day 18 guarded: `bash infrastructure/docker/migration-day4/scripts/run_day18_read_switch_guarded.sh`
> Day 18 hourly snapshot/trend: `bash infrastructure/docker/migration-day4/scripts/run_day18_read_switch_hourly.sh`
> Run Day 19 guarded: `bash infrastructure/docker/migration-day4/scripts/run_day19_read_switch_guarded.sh`
> Day 19 hourly snapshot/trend: `bash infrastructure/docker/migration-day4/scripts/run_day19_read_switch_hourly.sh`

### Ngày 20
- [ ] Tăng tổng traffic lên 80% (write + read tùy dịch vụ).
- [ ] Audit lại permission, secret rotation, rate limiting.

**Deliverables Ngày 20**: xem [DAY20_DELIVERABLES.md](DAY20_DELIVERABLES.md)

> Ghi chú Day 20: tăng traffic 80% được guardrail chặn cho đến khi Day 19 `READ_SWITCHED_50`.
> Run Day 20 guarded: `bash infrastructure/docker/migration-day4/scripts/run_day20_traffic_guarded.sh`
> Day 20 hourly snapshot/trend: `bash infrastructure/docker/migration-day4/scripts/run_day20_traffic_hourly.sh`

### Ngày 21 (Gate 3)
- [ ] Gate tuần 3: 80% ổn định >= 72h.
- [x] Compare report pass >= 99.5% bản ghi trong ngưỡng cho phép.
- [ ] Duyệt full cutover tuần 4.

**Deliverables Ngày 21**: xem [DAY21_DELIVERABLES.md](DAY21_DELIVERABLES.md)

> Ghi chú Day 21: Gate 3 được guardrail kiểm soát theo 80% stability >=72h và compare pass rate >=99.5%.
> Run Day 21 guarded: `bash infrastructure/docker/migration-day4/scripts/run_day21_gate3_guarded.sh`
> Day 21 hourly snapshot/trend: `bash infrastructure/docker/migration-day4/scripts/run_day21_gate3_hourly.sh`

---

## Tuần 4 (Ngày 22-30): 100% Cutover + Decommission

### Ngày 22-24
- [ ] Cutover 100% write/load sang OSS.
- [ ] Giữ shadow read từ legacy thêm 2-3 ngày để so sánh.

**Deliverables Ngày 22-24**: xem [DAY22_24_DELIVERABLES.md](DAY22_24_DELIVERABLES.md)

> Ghi chú Day 22-24: batch cutover 100% write/load + shadow read được guardrail chặn cho đến khi Day 21 Gate 3 `PASS`.
> Run Day 22-24 guarded: `bash infrastructure/docker/migration-day4/scripts/run_day22_24_cutover_guarded.sh`
> Day 22-24 hourly snapshot/trend: `bash infrastructure/docker/migration-day4/scripts/run_day22_24_cutover_hourly.sh`

### Ngày 25-26
- [ ] Cutover 100% read path sang OSS.
- [ ] Đóng dần tài nguyên legacy không còn sử dụng.

**Deliverables Ngày 25-26**: xem [DAY25_26_DELIVERABLES.md](DAY25_26_DELIVERABLES.md)

> Ghi chú Day 25-26: cutover read path 100% + đóng dần legacy được guardrail chặn cho đến khi Day 22-24 đạt `WRITE_LOAD_100_SHADOW_READ`.
> Run Day 25-26 guarded: `bash infrastructure/docker/migration-day4/scripts/run_day25_26_read_cutover_guarded.sh`
> Day 25-26 hourly snapshot/trend: `bash infrastructure/docker/migration-day4/scripts/run_day25_26_read_cutover_hourly.sh`

### Ngày 27
- [ ] Chạy full regression + performance suite.
- [ ] Verify dashboard SLO, alert, audit logs.

**Deliverables Ngày 27**: xem [DAY27_DELIVERABLES.md](DAY27_DELIVERABLES.md)

> Ghi chú Day 27: full validation chỉ `PASS` khi regression + performance + SLO/alert/audit đều đạt và Day 25-26 đã `READ_PATH_100_LEGACY_DRAINING`.
> Run Day 27 guarded: `bash infrastructure/docker/migration-day4/scripts/run_day27_validation_guarded.sh`
> Day 27 hourly snapshot/trend: `bash infrastructure/docker/migration-day4/scripts/run_day27_validation_hourly.sh`

### Ngày 28
- [ ] Freeze thay đổi lớn, theo dõi ổn định 24h.
- [ ] Chốt báo cáo post-cutover.

**Deliverables Ngày 28**: xem [DAY28_DELIVERABLES.md](DAY28_DELIVERABLES.md)

> Ghi chú Day 28: freeze chỉ `PASS` khi Day 27 đã `VALIDATED_FOR_FREEZE`, freeze window đủ 24h, không có thay đổi critical, SLO/incident ổn định và báo cáo post-cutover đã sẵn sàng.
> Run Day 28 guarded: `bash infrastructure/docker/migration-day4/scripts/run_day28_freeze_guarded.sh`
> Day 28 hourly snapshot/trend: `bash infrastructure/docker/migration-day4/scripts/run_day28_freeze_hourly.sh`

### Ngày 29
- [ ] Decommission có kiểm soát: cron/job cũ, route cũ, config cũ.
- [ ] Backup config + runbook + rollback snapshot cuối.

**Deliverables Ngày 29**: xem [DAY29_DELIVERABLES.md](DAY29_DELIVERABLES.md)

> Ghi chú Day 29: decommission chỉ `PASS` khi Day 28 đã `FREEZE_LOCKED_REPORT_FINALIZED`, tài nguyên legacy được tháo dỡ có kiểm soát, và backup/runbook/rollback snapshot hoàn tất.
> Run Day 29 guarded: `bash infrastructure/docker/migration-day4/scripts/run_day29_decommission_guarded.sh`
> Day 29 hourly snapshot/trend: `bash infrastructure/docker/migration-day4/scripts/run_day29_decommission_hourly.sh`

### Ngày 30 (Go-Live Closure)
- [ ] Ký biên bản nghiệm thu kỹ thuật.
- [ ] Tổng kết lessons learned.
- [ ] Chuyển sang phase tối ưu chi phí/hiệu năng.

**Deliverables Ngày 30**: xem [DAY30_DELIVERABLES.md](DAY30_DELIVERABLES.md)

> Ghi chú Day 30: closure chỉ `PASS` khi Day 29 đã `DECOMMISSIONED_WITH_BACKUP` và toàn bộ hạng mục nghiệm thu/lessons learned/optimization kickoff hoàn tất.
> Run Day 30 guarded: `bash infrastructure/docker/migration-day4/scripts/run_day30_closure_guarded.sh`
> Day 30 hourly snapshot/trend: `bash infrastructure/docker/migration-day4/scripts/run_day30_closure_hourly.sh`

---

## Exit Criteria (bắt buộc)
- [ ] SLO đạt trong 7 ngày liên tục sau cutover.
- [ ] Data quality checks pass >= ngưỡng đã định.
- [ ] Không còn dependency runtime vào legacy.
- [ ] Runbook on-call và rollback được kiểm thử.

## Rollback Criteria
- [ ] Error rate tăng > ngưỡng 2 lần liên tiếp trong 10 phút.
- [ ] Mismatch dữ liệu critical vượt ngưỡng.
- [ ] Latency p99 vượt ngưỡng bảo vệ SLA.

## Gợi ý phân công team (3-6 người)
- 1 Data Engineer (Spark/Airflow)
- 1 Backend Engineer (FastAPI/adapter)
- 1 Platform/DevOps (K8s/monitoring)
- 1 QA/Analytics (data compare + regression)
- 1 Tech lead kiêm Incident commander (part-time)
