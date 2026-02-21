#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) START DAY16 HOURLY ==="

REPORT_DIR="documentation/migration/reports"
HISTORY_DIR="$REPORT_DIR/history"
LATEST_FILE="$REPORT_DIR/DAY16_OBSERVATION_REPORT.json"
WATCHER_FILE="$REPORT_DIR/DAY16_WATCHER_RESULT.json"
TREND_FILE="$REPORT_DIR/DAY16_OBSERVATION_TREND_24H.json"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
HISTORY_FILE="$HISTORY_DIR/DAY16_OBSERVATION_REPORT_${STAMP}.json"

mkdir -p "$REPORT_DIR" "$HISTORY_DIR"

bash infrastructure/docker/migration-day4/scripts/run_day16_observation.sh
cp "$LATEST_FILE" "$HISTORY_FILE"

PYTHONPATH=. python -m shared.platform.migration_templates.day16_observation_trend \
  --history-dir "$HISTORY_DIR" \
  --latest-file "$LATEST_FILE" \
  --window-hours 24 \
  --output "$TREND_FILE"

PYTHONPATH=. python -m shared.platform.migration_templates.day16_observation_watcher \
  --day16-report "$LATEST_FILE" \
  --output "$WATCHER_FILE" \
  --state-file "$HISTORY_DIR/DAY16_OBSERVATION_STATE.json" \
  --transition-log "$HISTORY_DIR/DAY16_OBSERVATION_TRANSITIONS.jsonl"

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$LATEST_FILE")"
  TREND_STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$TREND_FILE")"
  RUNS="$(jq -r '.summary.total_runs // 0' "$TREND_FILE")"
  READY_RATE="$(jq -r '.summary.ready_rate_pct // 0' "$TREND_FILE")"
  BLOCKERS="$(jq -r '.summary.blockers | join(",")' "$LATEST_FILE")"
  TRANSITION="$(jq -r '.transition.transition_type // "none"' "$WATCHER_FILE")"
  echo "[INFO] day16_status=$STATUS trend_status=$TREND_STATUS runs_24h=$RUNS ready_rate_24h=$READY_RATE blockers=${BLOCKERS:-none} transition=$TRANSITION"
fi

echo "[INFO] history snapshot: $HISTORY_FILE"
echo "[INFO] watcher result: $WATCHER_FILE"
echo "[DONE] Day 16 hourly observation snapshot completed"
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) END DAY16 HOURLY ==="

exit 0
