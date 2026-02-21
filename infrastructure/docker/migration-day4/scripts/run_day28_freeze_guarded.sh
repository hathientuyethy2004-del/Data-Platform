#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY28_FREEZE_REPORT.json"
ENV_FILE="infrastructure/docker/migration-day4/.env.day28.freeze.example"
WATCHER_FILE="documentation/migration/reports/DAY28_WATCHER_RESULT.json"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day28_freeze_runner \
  --env-file "$ENV_FILE" \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

PYTHONPATH=. python -m shared.platform.migration_templates.day28_freeze_watcher \
  --report "$OUT_FILE" \
  --checklist documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md \
  --output "$WATCHER_FILE"

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  FREEZE_ENABLED="$(jq -r '.checks.freeze_window_enabled.status // "FAIL"' "$OUT_FILE")"
  FREEZE_24H="$(jq -r '.checks.freeze_observed_24h.status // "FAIL"' "$OUT_FILE")"
  NO_CRITICAL="$(jq -r '.checks.no_critical_changes.status // "FAIL"' "$OUT_FILE")"
  SLO="$(jq -r '.checks.slo_stable_24h.status // "FAIL"' "$OUT_FILE")"
  NO_SEV="$(jq -r '.checks.no_sev1_sev2_24h.status // "FAIL"' "$OUT_FILE")"
  REPORT_READY="$(jq -r '.checks.post_cutover_report_ready.status // "FAIL"' "$OUT_FILE")"
  BLK="$(jq -r '.freeze.blockers | join(",")' "$OUT_FILE")"
  echo "[INFO] day28_status=$STATUS freeze_enabled=$FREEZE_ENABLED freeze_24h=$FREEZE_24H no_critical_changes=$NO_CRITICAL slo_24h=$SLO no_sev1_2_24h=$NO_SEV post_cutover_report=$REPORT_READY blockers=${BLK:-none}"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 28 freeze checks passed"
else
  echo "[WARN] Day 28 freeze checks blocked by guardrails"
fi

echo "[INFO] watcher report: $WATCHER_FILE"

exit 0
