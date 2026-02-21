# Migration Adapter Templates (Quick Start)

Bộ template này giúp team chuyển đổi từ legacy code sang open-source stack theo cách an toàn (strangler pattern).

## File có sẵn
- `ports.py`: định nghĩa interface chuẩn cho ingestion/quality/serving.
- `feature_flags.py`: bật/tắt đường chạy OSS qua biến môi trường.
- `adapters.py`: adapter mẫu cho legacy và OSS implementation.
- `router.py`: router chọn adapter theo flag.
- `day5_smoke_runner.py`: chạy smoke E2E và sinh baseline compare report Day 5.
- `compare_utils.py`: normalize & compare record cho mismatch schema/timezone/rounding/null semantics.
- `day7_gate_runner.py`: đánh giá Gate 1 (>=24h ổn định + không mismatch critical).
- `day7_gate_watcher.py`: đọc report Gate 1 và tự cập nhật checklist Day 7.
- `day8_canary_runner.py`: kiểm cấu hình canary 10% + snapshot monitoring Day 8.
- `day8_canary_trend.py`: tổng hợp trend Day 8 trong cửa sổ 24h từ history runs.
- `day9_readiness_runner.py`: đánh giá GO/NO_GO để tăng canary Day 10 lên 20%.
- `day10_rollout_runner.py`: áp dụng rollout 20% có guardrail + load/backpressure checks.
- `day10_rollout_watcher.py`: tự cập nhật checklist Day 10 theo trạng thái rollout.
- `day11_tuning_runner.py`: phân tích bottleneck và tune alert threshold Day 11.
- `day12_post_tuning_validator.py`: xác thực hiệu quả tuning (false-positive/false-negative) cho Day 12.
- `day13_chaos_runner.py`: chaos validation cho restart/network blip/retry/idempotency/integrity.
- `day14_gate2_runner.py`: đánh giá Gate 2 (48h stability + Sev-1/2 + quyết định scale Week 3).
- `day14_gate2_watcher.py`: tự cập nhật checklist Day 14 theo trạng thái Gate 2 và ghi transition audit.
- `day15_scale_runner.py`: đánh giá scale-up Day 15 lên 50% với guardrail sau Gate 2 PASS.
- `day15_scale_watcher.py`: tự cập nhật checklist Day 15-16 từ kết quả scale report.
- `day15_compare_trend.py`: tổng hợp trend 24h cho Day 15 hourly compare snapshots.
- `day16_observation_runner.py`: đánh giá readiness Day 16 để mở khóa Day 17 read-switch có kiểm soát.
- `day16_observation_trend.py`: tổng hợp trend 24h Day 16 từ hourly observation snapshots.
- `day16_observation_watcher.py`: ghi transition audit Day 16 (`HOLD` -> `READY_FOR_DAY17`).
- `day17_read_switch_runner.py`: đánh giá guarded read switch 10% cho Day 17.
- `day17_read_switch_watcher.py`: tự cập nhật checklist Day 17 từ read-switch report.
- `day17_read_switch_trend.py`: tổng hợp trend 24h Day 17 và theo dõi thời điểm chuyển BLOCKED -> READ_SWITCHED_10.
- `day18_read_switch_runner.py`: đánh giá guarded read switch tăng lên 30% cho Day 18.
- `day18_read_switch_watcher.py`: tự cập nhật checklist Day 18-19 từ Day 18 report.
- `day18_read_switch_trend.py`: tổng hợp trend 24h Day 18 và theo dõi thời điểm chuyển BLOCKED -> READ_SWITCHED_30.
- `day19_read_switch_runner.py`: đánh giá guarded read switch tăng lên 50% cho Day 19.
- `day19_read_switch_watcher.py`: tự cập nhật checklist Day 18-19 theo kết quả Day 19.
- `day20_traffic_runner.py`: đánh giá guarded tăng tổng traffic lên 80% cho Day 20.
- `day20_traffic_watcher.py`: tự cập nhật checklist Day 20 theo kết quả traffic report.
- `day21_gate3_runner.py`: đánh giá Gate 3 có kiểm soát cho Day 21 (80%/72h + compare >=99.5%).
- `day21_gate3_watcher.py`: tự cập nhật checklist Day 21 theo kết quả Gate 3.
- `day22_24_cutover_runner.py`: đánh giá guarded batch Day 22-24 cho cutover 100% write/load + shadow read.
- `day22_24_cutover_watcher.py`: tự cập nhật checklist Day 22-24 theo cutover report.
- `day25_26_read_cutover_runner.py`: đánh giá guarded cutover 100% read path + phase-down legacy resources.
- `day25_26_read_cutover_watcher.py`: tự cập nhật checklist Day 25-26 theo read-cutover report.
- `day27_validation_runner.py`: đánh giá guarded Day 27 cho full regression + performance suite + SLO/audit verify.
- `day27_validation_watcher.py`: tự cập nhật checklist Day 27 theo validation report.
- `day27_validation_trend.py`: tổng hợp trend 24h Day 27 và theo dõi thời điểm chuyển BLOCKED -> VALIDATED_FOR_FREEZE.
- `day28_freeze_runner.py`: đánh giá guarded Day 28 cho freeze 24h + closure post-cutover report.
- `day28_freeze_watcher.py`: tự cập nhật checklist Day 28 theo freeze report.
- `day28_freeze_trend.py`: tổng hợp trend 24h Day 28 và theo dõi thời điểm chuyển BLOCKED -> FREEZE_LOCKED_REPORT_FINALIZED.
- `day29_decommission_runner.py`: đánh giá guarded Day 29 cho decommission legacy có kiểm soát + backup/runbook/rollback snapshot.
- `day29_decommission_watcher.py`: tự cập nhật checklist Day 29 theo decommission report.
- `day29_decommission_trend.py`: tổng hợp trend 24h Day 29 và theo dõi thời điểm chuyển BLOCKED -> DECOMMISSIONED_WITH_BACKUP.
- `day30_closure_runner.py`: đánh giá guarded Day 30 cho go-live closure (technical acceptance + lessons learned + optimization kickoff).
- `day30_closure_watcher.py`: tự cập nhật checklist Day 30 theo closure report.
- `day30_closure_trend.py`: tổng hợp trend 24h Day 30 và theo dõi thời điểm chuyển BLOCKED -> GO_LIVE_CLOSED.

## Day 7 automation (gợi ý vận hành)
- Chạy wrapper hourly: `bash infrastructure/docker/migration-day4/scripts/run_day7_gate_hourly.sh`
- Cài cron mẫu: `infrastructure/docker/migration-day4/scripts/day7_gate1.cron.example`
- Kết quả latest: `documentation/migration/reports/DAY7_GATE1_REPORT.json`
- Kết quả watcher: `documentation/migration/reports/DAY7_WATCHER_RESULT.json`
- Lịch sử runs: `documentation/migration/reports/history/`
- Audit transition: `documentation/migration/reports/history/DAY7_GATE1_TRANSITIONS.jsonl`
- State tracking: `documentation/migration/reports/history/DAY7_GATE1_STATE.json`
- Closure when PASS: `documentation/migration/DAY7_GATE1_CLOSURE.md`

## Day 8 canary setup
- Env profile: `infrastructure/docker/migration-day4/.env.day8.canary10.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day8_canary_setup.sh`
- Output report: `documentation/migration/reports/DAY8_CANARY_STATUS.json`
- Hourly script: `bash infrastructure/docker/migration-day4/scripts/run_day8_canary_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day8_canary_hourly.cron.example`
- Trend report (24h): `documentation/migration/reports/DAY8_CANARY_TREND_24H.json`

## Day 9 readiness check
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day9_readiness_check.sh`
- Output report: `documentation/migration/reports/DAY9_STABILITY_REPORT.json`

## Day 10 guarded rollout
- Env profile: `infrastructure/docker/migration-day4/.env.day10.canary20.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day10_rollout_guarded.sh`
- Output report: `documentation/migration/reports/DAY10_ROLLOUT_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY10_WATCHER_RESULT.json`
- Active profile when applied: `infrastructure/docker/migration-day4/.env.day10.active`

## Day 11 tuning
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day11_tuning.sh`
- Output report: `documentation/migration/reports/DAY11_TUNING_REPORT.json`
- Tuned alert policy: `infrastructure/docker/migration-day4/alert_thresholds.day11.tuned.json`

## Day 12 post-tuning validation
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day12_post_tuning_validation.sh`
- Sample observations: `documentation/migration/reports/DAY12_ALERT_OBSERVATIONS_SAMPLE.json`
- Output report: `documentation/migration/reports/DAY12_ALERT_VALIDATION_REPORT.json`

## Day 13 chaos validation
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day13_chaos_validation.sh`
- Output report: `documentation/migration/reports/DAY13_CHAOS_REPORT.json`

## Day 14 Gate 2
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day14_gate2.sh`
- Hourly re-check script: `bash infrastructure/docker/migration-day4/scripts/run_day14_gate2_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day14_gate2_hourly.cron.example`
- Incident log input: `documentation/migration/reports/DAY14_INCIDENT_LOG.json`
- Output report: `documentation/migration/reports/DAY14_GATE2_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY14_WATCHER_RESULT.json`

## Day 15 guarded scale-up
- Env profile: `infrastructure/docker/migration-day4/.env.day15.scale50.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day15_scale_guarded.sh`
- Hourly compare script: `bash infrastructure/docker/migration-day4/scripts/run_day15_compare_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day15_compare_hourly.cron.example`
- Output report: `documentation/migration/reports/DAY15_SCALE_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY15_WATCHER_RESULT.json`
- Trend report (24h): `documentation/migration/reports/DAY15_COMPARE_TREND_24H.json`
- Active profile when applied: `infrastructure/docker/migration-day4/.env.day15.active`

## Day 16 observation readiness
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day16_observation.sh`
- Output report: `documentation/migration/reports/DAY16_OBSERVATION_REPORT.json`
- Hourly observation script: `bash infrastructure/docker/migration-day4/scripts/run_day16_observation_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day16_observation_hourly.cron.example`
- Trend report (24h): `documentation/migration/reports/DAY16_OBSERVATION_TREND_24H.json`
- Watcher report: `documentation/migration/reports/DAY16_WATCHER_RESULT.json`
- Transition audit: `documentation/migration/reports/history/DAY16_OBSERVATION_TRANSITIONS.jsonl`

## Day 17 guarded read switch
- Env profile: `infrastructure/docker/migration-day4/.env.day17.read10.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day17_read_switch_guarded.sh`
- Hourly script: `bash infrastructure/docker/migration-day4/scripts/run_day17_read_switch_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day17_read_switch_hourly.cron.example`
- Output report: `documentation/migration/reports/DAY17_READ_SWITCH_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY17_WATCHER_RESULT.json`
- Trend report (24h): `documentation/migration/reports/DAY17_READ_SWITCH_TREND_24H.json`

## Day 18 guarded read switch
- Env profile: `infrastructure/docker/migration-day4/.env.day18.read30.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day18_read_switch_guarded.sh`
- Output report: `documentation/migration/reports/DAY18_READ_SWITCH_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY18_WATCHER_RESULT.json`
- Hourly script: `bash infrastructure/docker/migration-day4/scripts/run_day18_read_switch_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day18_read_switch_hourly.cron.example`
- Trend report (24h): `documentation/migration/reports/DAY18_READ_SWITCH_TREND_24H.json`

## Day 19 guarded read switch
- Env profile: `infrastructure/docker/migration-day4/.env.day19.read50.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day19_read_switch_guarded.sh`
- Output report: `documentation/migration/reports/DAY19_READ_SWITCH_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY19_WATCHER_RESULT.json`
- Hourly script: `bash infrastructure/docker/migration-day4/scripts/run_day19_read_switch_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day19_read_switch_hourly.cron.example`
- Trend report (24h): `documentation/migration/reports/DAY19_READ_SWITCH_TREND_24H.json`

## Day 20 guarded traffic
- Env profile: `infrastructure/docker/migration-day4/.env.day20.traffic80.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day20_traffic_guarded.sh`
- Output report: `documentation/migration/reports/DAY20_TRAFFIC_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY20_WATCHER_RESULT.json`
- Hourly script: `bash infrastructure/docker/migration-day4/scripts/run_day20_traffic_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day20_traffic_hourly.cron.example`
- Trend report (24h): `documentation/migration/reports/DAY20_TRAFFIC_TREND_24H.json`
- Active profile when applied: `infrastructure/docker/migration-day4/.env.day20.active`

## Day 21 Gate 3
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day21_gate3_guarded.sh`
- Output report: `documentation/migration/reports/DAY21_GATE3_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY21_WATCHER_RESULT.json`
- Hourly script: `bash infrastructure/docker/migration-day4/scripts/run_day21_gate3_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day21_gate3_hourly.cron.example`
- Trend report (24h): `documentation/migration/reports/DAY21_GATE3_TREND_24H.json`

## Day 22-24 guarded batch cutover
- Env profile: `infrastructure/docker/migration-day4/.env.day22_24.cutover100.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day22_24_cutover_guarded.sh`
- Output report: `documentation/migration/reports/DAY22_24_CUTOVER_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY22_24_WATCHER_RESULT.json`
- Hourly script: `bash infrastructure/docker/migration-day4/scripts/run_day22_24_cutover_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day22_24_cutover_hourly.cron.example`
- Trend report (24h): `documentation/migration/reports/DAY22_24_CUTOVER_TREND_24H.json`
- Active profile when applied: `infrastructure/docker/migration-day4/.env.day22_24.active`

## Day 25-26 guarded read cutover
- Env profile: `infrastructure/docker/migration-day4/.env.day25_26.read100.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day25_26_read_cutover_guarded.sh`
- Output report: `documentation/migration/reports/DAY25_26_READ_CUTOVER_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY25_26_WATCHER_RESULT.json`
- Hourly script: `bash infrastructure/docker/migration-day4/scripts/run_day25_26_read_cutover_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day25_26_read_cutover_hourly.cron.example`
- Trend report (24h): `documentation/migration/reports/DAY25_26_READ_CUTOVER_TREND_24H.json`
- Active profile when applied: `infrastructure/docker/migration-day4/.env.day25_26.active`

## Day 27 guarded validation
- Env profile: `infrastructure/docker/migration-day4/.env.day27.validation.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day27_validation_guarded.sh`
- Output report: `documentation/migration/reports/DAY27_VALIDATION_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY27_WATCHER_RESULT.json`
- Hourly script: `bash infrastructure/docker/migration-day4/scripts/run_day27_validation_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day27_validation_hourly.cron.example`
- Trend report (24h): `documentation/migration/reports/DAY27_VALIDATION_TREND_24H.json`

## Day 28 guarded freeze
- Env profile: `infrastructure/docker/migration-day4/.env.day28.freeze.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day28_freeze_guarded.sh`
- Output report: `documentation/migration/reports/DAY28_FREEZE_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY28_WATCHER_RESULT.json`
- Hourly script: `bash infrastructure/docker/migration-day4/scripts/run_day28_freeze_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day28_freeze_hourly.cron.example`
- Trend report (24h): `documentation/migration/reports/DAY28_FREEZE_TREND_24H.json`

## Day 29 guarded decommission
- Env profile: `infrastructure/docker/migration-day4/.env.day29.decommission.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day29_decommission_guarded.sh`
- Output report: `documentation/migration/reports/DAY29_DECOMMISSION_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY29_WATCHER_RESULT.json`
- Hourly script: `bash infrastructure/docker/migration-day4/scripts/run_day29_decommission_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day29_decommission_hourly.cron.example`
- Trend report (24h): `documentation/migration/reports/DAY29_DECOMMISSION_TREND_24H.json`

## Day 30 guarded closure
- Env profile: `infrastructure/docker/migration-day4/.env.day30.closure.example`
- Run script: `bash infrastructure/docker/migration-day4/scripts/run_day30_closure_guarded.sh`
- Output report: `documentation/migration/reports/DAY30_CLOSURE_REPORT.json`
- Watcher report: `documentation/migration/reports/DAY30_WATCHER_RESULT.json`
- Hourly script: `bash infrastructure/docker/migration-day4/scripts/run_day30_closure_hourly.sh`
- Hourly cron template: `infrastructure/docker/migration-day4/scripts/day30_closure_hourly.cron.example`
- Trend report (24h): `documentation/migration/reports/DAY30_CLOSURE_TREND_24H.json`

## Migration cron health check
- Check script: `bash infrastructure/docker/migration-day4/scripts/check_migration_cron_health.sh`
- Optional window (minutes): `bash infrastructure/docker/migration-day4/scripts/check_migration_cron_health.sh 90`
- JSON status output: `bash infrastructure/docker/migration-day4/scripts/check_migration_cron_health.sh --window-minutes 60 --json-output documentation/migration/reports/MIGRATION_CRON_HEALTH_STATUS.json`
- Flat row output (BI-friendly): `bash infrastructure/docker/migration-day4/scripts/check_migration_cron_health.sh --window-minutes 60 --flat-output documentation/migration/reports/MIGRATION_CRON_HEALTH_PANEL_ROW.json`
- BI panel key mapping spec: `documentation/migration/reports/MIGRATION_CRON_HEALTH_PANEL_SPEC.json`
- Reads log freshness from:
    - `documentation/migration/reports/DAY14_GATE2_CRON.log`
    - `documentation/migration/reports/DAY15_COMPARE_CRON.log`
    - `documentation/migration/reports/DAY27_VALIDATION_CRON.log`
    - `documentation/migration/reports/DAY28_FREEZE_CRON.log`
    - `documentation/migration/reports/DAY29_DECOMMISSION_CRON.log`
    - `documentation/migration/reports/DAY30_CLOSURE_CRON.log`

## Unified hourly log tail
- Tail latest Day 14/15/16 blocks in one command: `bash infrastructure/docker/migration-day4/scripts/tail_migration_hourly_logs.sh`
- Optional fallback lines when marker block not found: `bash infrastructure/docker/migration-day4/scripts/tail_migration_hourly_logs.sh 40`

## Cách tích hợp vào 1 product
1. Copy các file này vào module product của bạn (vd: `products/<name>/src/migration/`).
2. Thay logic stub trong `Legacy*Adapter` bằng code cũ hiện có.
3. Thay logic stub trong `OSS*Adapter` bằng code mới (Kafka/Airflow/Spark/Trino...).
4. Ở entrypoint service, build router từ env:

```python
from shared.platform.migration_templates.feature_flags import MigrationFlags
from shared.platform.migration_templates.router import MigrationRouter

flags = MigrationFlags.from_env()
router = MigrationRouter.build(flags)
```

5. Đổi flow xử lý chính sang gọi router:

```python
def process_events(events):
    report = router.process_events(events)
    return report
```

## Biến môi trường
- `USE_OSS_INGESTION=true|false`
- `USE_OSS_QUALITY=true|false`
- `USE_OSS_SERVING=true|false`
- `DUAL_RUN_ENABLED=true|false`

## Gợi ý rollout
- Giai đoạn 1: tất cả flag = `false` (legacy 100%).
- Giai đoạn 2: bật từng flag theo canary 10% -> 20% -> 50%.
- Giai đoạn 3: OSS 100%, giữ fallback ngắn hạn.

## Note
- Template này là skeleton để bắt đầu nhanh.
- Trước production: bổ sung timeout/retry/idempotency/log correlation và metrics compare.
