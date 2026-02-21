#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) START DAY21 HOURLY ==="

REPORT_DIR="documentation/migration/reports"
HISTORY_DIR="$REPORT_DIR/history"
LATEST_FILE="$REPORT_DIR/DAY21_GATE3_REPORT.json"
WATCHER_FILE="$REPORT_DIR/DAY21_WATCHER_RESULT.json"
TREND_FILE="$REPORT_DIR/DAY21_GATE3_TREND_24H.json"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
HISTORY_FILE="$HISTORY_DIR/DAY21_GATE3_REPORT_${STAMP}.json"

mkdir -p "$REPORT_DIR" "$HISTORY_DIR"

bash infrastructure/docker/migration-day4/scripts/run_day21_gate3_guarded.sh
cp "$LATEST_FILE" "$HISTORY_FILE"

PYTHONPATH=. python -m shared.platform.migration_templates.day21_gate3_trend \
  --history-dir "$HISTORY_DIR" \
  --latest-file "$LATEST_FILE" \
  --window-hours 24 \
  --output "$TREND_FILE"

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$LATEST_FILE")"
  TREND_STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$TREND_FILE")"
  RUNS="$(jq -r '.summary.total_runs // 0' "$TREND_FILE")"
  PASS_RATE="$(jq -r '.summary.pass_rate_pct // 0' "$TREND_FILE")"
  TRANS_AT="$(jq -r '.summary.last_transition_to_pass_at // ""' "$TREND_FILE")"
  BLOCKERS="$(jq -r '.summary.blockers | join(",")' "$LATEST_FILE")"
  echo "[INFO] day21_status=$STATUS trend_status=$TREND_STATUS runs_24h=$RUNS pass_rate_24h=$PASS_RATE blockers=${BLOCKERS:-none} last_transition=${TRANS_AT:-none}"
fi

echo "[INFO] history snapshot: $HISTORY_FILE"
echo "[INFO] watcher result: $WATCHER_FILE"
echo "[DONE] Day 21 hourly gate snapshot completed"
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) END DAY21 HOURLY ==="

exit 0
