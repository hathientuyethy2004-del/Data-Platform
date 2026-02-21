#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

REPORT_DIR="documentation/migration/reports"
HISTORY_DIR="$REPORT_DIR/history"
LATEST_FILE="$REPORT_DIR/DAY7_GATE1_REPORT.json"
WATCHER_FILE="$REPORT_DIR/DAY7_WATCHER_RESULT.json"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
HISTORY_FILE="$HISTORY_DIR/DAY7_GATE1_REPORT_${STAMP}.json"

mkdir -p "$REPORT_DIR" "$HISTORY_DIR"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day7_gate_runner \
  --output "$LATEST_FILE"
RUN_CODE=$?
set -e

PYTHONPATH=. python -m shared.platform.migration_templates.day7_gate_watcher \
  --gate-report "$LATEST_FILE" \
  --checklist documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md \
  --output "$WATCHER_FILE"

cp "$LATEST_FILE" "$HISTORY_FILE"

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$LATEST_FILE")"
  OBS_HOURS="$(jq -r '.checks.dual_run_staging_stable_24h.observed_hours // "n/a"' "$LATEST_FILE")"
  REMAIN_HOURS="$(jq -r '.checks.dual_run_staging_stable_24h.remaining_hours_to_gate // "n/a"' "$LATEST_FILE")"
  ETA_PASS="$(jq -r '.checks.dual_run_staging_stable_24h.estimated_pass_at_utc // "n/a"' "$LATEST_FILE")"
  PASSED_TS="$(jq -r '.audit.gate_passed_timestamp // ""' "$LATEST_FILE")"
  echo "[INFO] gate_status=$STATUS observed_hours=$OBS_HOURS remaining_hours=$REMAIN_HOURS eta_pass=$ETA_PASS run_code=$RUN_CODE gate_passed_timestamp=${PASSED_TS:-none}"
else
  echo "[INFO] gate report generated at $LATEST_FILE (jq not found, skipped summary parsing)"
fi

echo "[INFO] history snapshot: $HISTORY_FILE"
echo "[INFO] watcher result: $WATCHER_FILE"

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Gate 1 PASS"
else
  echo "[WARN] Gate 1 not pass yet (expected while <24h stability window)"
fi

exit 0
