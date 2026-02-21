#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY27_VALIDATION_REPORT.json"
ENV_FILE="infrastructure/docker/migration-day4/.env.day27.validation.example"
WATCHER_FILE="documentation/migration/reports/DAY27_WATCHER_RESULT.json"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day27_validation_runner \
  --env-file "$ENV_FILE" \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

PYTHONPATH=. python -m shared.platform.migration_templates.day27_validation_watcher \
  --report "$OUT_FILE" \
  --checklist documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md \
  --output "$WATCHER_FILE"

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  REG="$(jq -r '.checks.full_regression_suite_passed.status // "FAIL"' "$OUT_FILE")"
  PERF="$(jq -r '.checks.performance_suite_passed.status // "FAIL"' "$OUT_FILE")"
  PERF_GUARD="$(jq -r '.checks.performance_guardrails.status // "FAIL"' "$OUT_FILE")"
  SLO="$(jq -r '.checks.slo_dashboard_passed.status // "FAIL"' "$OUT_FILE")"
  ALERTS="$(jq -r '.checks.alerts_verified.status // "FAIL"' "$OUT_FILE")"
  AUDIT="$(jq -r '.checks.audit_logs_verified.status // "FAIL"' "$OUT_FILE")"
  BLK="$(jq -r '.validation.blockers | join(",")' "$OUT_FILE")"
  echo "[INFO] day27_status=$STATUS regression=$REG performance=$PERF performance_guardrails=$PERF_GUARD slo=$SLO alerts=$ALERTS audit_logs=$AUDIT blockers=${BLK:-none}"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 27 validation passed"
else
  echo "[WARN] Day 27 validation blocked by guardrails"
fi

echo "[INFO] watcher report: $WATCHER_FILE"

exit 0
