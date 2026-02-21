#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) START DAY14 HOURLY ==="

REPORT_DIR="documentation/migration/reports"
HISTORY_DIR="$REPORT_DIR/history"
LATEST_FILE="$REPORT_DIR/DAY14_GATE2_REPORT.json"
WATCHER_FILE="$REPORT_DIR/DAY14_WATCHER_RESULT.json"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
HISTORY_FILE="$HISTORY_DIR/DAY14_GATE2_REPORT_${STAMP}.json"

mkdir -p "$REPORT_DIR" "$HISTORY_DIR"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day14_gate2_runner \
  --output "$LATEST_FILE"
RUN_CODE=$?
set -e

PYTHONPATH=. python -m shared.platform.migration_templates.day14_gate2_watcher \
  --gate-report "$LATEST_FILE" \
  --checklist documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md \
  --output "$WATCHER_FILE" \
  --state-file "$HISTORY_DIR/DAY14_GATE2_STATE.json" \
  --transition-log "$HISTORY_DIR/DAY14_GATE2_TRANSITIONS.jsonl"

cp "$LATEST_FILE" "$HISTORY_FILE"

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$LATEST_FILE")"
  HRS="$(jq -r '.checks.canary_20_stable_48h.observed_hours // "n/a"' "$LATEST_FILE")"
  REMAIN="$(jq -r '.checks.canary_20_stable_48h.remaining_hours // "n/a"' "$LATEST_FILE")"
  ETA="$(jq -r '.checks.canary_20_stable_48h.estimated_gate2_at_utc // "n/a"' "$LATEST_FILE")"
  BLK="$(jq -r '.summary.blockers | join(",")' "$LATEST_FILE")"
  TRANS="$(jq -r '.transition.transition_type // "none"' "$WATCHER_FILE")"
  echo "[INFO] gate2_status=$STATUS observed_hours=$HRS remaining_hours=$REMAIN eta=$ETA blockers=${BLK:-none} transition=$TRANS run_code=$RUN_CODE"
fi

echo "[INFO] history snapshot: $HISTORY_FILE"
echo "[INFO] watcher result: $WATCHER_FILE"

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 14 Gate 2 PASS"
else
  echo "[WARN] Day 14 Gate 2 not pass yet"
fi

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) END DAY14 HOURLY ==="

exit 0
