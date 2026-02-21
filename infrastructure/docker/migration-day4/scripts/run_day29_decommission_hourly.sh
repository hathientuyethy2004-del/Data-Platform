#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) START DAY29 HOURLY ==="

REPORT_DIR="documentation/migration/reports"
HISTORY_DIR="$REPORT_DIR/history"
LATEST_FILE="$REPORT_DIR/DAY29_DECOMMISSION_REPORT.json"
WATCHER_FILE="$REPORT_DIR/DAY29_WATCHER_RESULT.json"
TREND_FILE="$REPORT_DIR/DAY29_DECOMMISSION_TREND_24H.json"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
HISTORY_FILE="$HISTORY_DIR/DAY29_DECOMMISSION_REPORT_${STAMP}.json"

mkdir -p "$REPORT_DIR" "$HISTORY_DIR"

bash infrastructure/docker/migration-day4/scripts/run_day29_decommission_guarded.sh
cp "$LATEST_FILE" "$HISTORY_FILE"

PYTHONPATH=. python -m shared.platform.migration_templates.day29_decommission_trend \
  --history-dir "$HISTORY_DIR" \
  --latest-file "$LATEST_FILE" \
  --window-hours 24 \
  --output "$TREND_FILE"

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$LATEST_FILE")"
  TREND_STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$TREND_FILE")"
  RUNS="$(jq -r '.summary.total_runs // 0' "$TREND_FILE")"
  RATE="$(jq -r '.summary.decommissioned_rate_pct // 0' "$TREND_FILE")"
  TRANS_AT="$(jq -r '.summary.last_transition_to_decommissioned_with_backup_at // ""' "$TREND_FILE")"
  BLOCKERS="$(jq -r '.decommission.blockers | join(",")' "$LATEST_FILE")"
  echo "[INFO] day29_status=$STATUS trend_status=$TREND_STATUS runs_24h=$RUNS decommissioned_rate_24h=$RATE blockers=${BLOCKERS:-none} last_transition=${TRANS_AT:-none}"
fi

echo "[INFO] history snapshot: $HISTORY_FILE"
echo "[INFO] watcher result: $WATCHER_FILE"
echo "[DONE] Day29 hourly decommission snapshot completed"
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) END DAY29 HOURLY ==="

exit 0
