#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) START DAY15 HOURLY ==="

REPORT_DIR="documentation/migration/reports"
HISTORY_DIR="$REPORT_DIR/history"
LATEST_FILE="$REPORT_DIR/DAY15_SCALE_REPORT.json"
WATCHER_FILE="$REPORT_DIR/DAY15_WATCHER_RESULT.json"
TREND_FILE="$REPORT_DIR/DAY15_COMPARE_TREND_24H.json"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
HISTORY_FILE="$HISTORY_DIR/DAY15_SCALE_REPORT_${STAMP}.json"

mkdir -p "$REPORT_DIR" "$HISTORY_DIR"

bash infrastructure/docker/migration-day4/scripts/run_day15_scale_guarded.sh
cp "$LATEST_FILE" "$HISTORY_FILE"

PYTHONPATH=. python -m shared.platform.migration_templates.day15_compare_trend \
  --history-dir "$HISTORY_DIR" \
  --latest-file "$LATEST_FILE" \
  --window-hours 24 \
  --output "$TREND_FILE"

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$LATEST_FILE")"
  TREND_STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$TREND_FILE")"
  RUNS="$(jq -r '.summary.total_runs // 0' "$TREND_FILE")"
  COMPARE_PASS_RATE="$(jq -r '.summary.compare_pass_rate_pct // 0' "$TREND_FILE")"
  BLOCKERS="$(jq -r '.rollout.blockers | join(",")' "$LATEST_FILE")"
  echo "[INFO] day15_status=$STATUS trend_status=$TREND_STATUS runs_24h=$RUNS compare_pass_rate_24h=$COMPARE_PASS_RATE blockers=${BLOCKERS:-none}"
fi

echo "[INFO] history snapshot: $HISTORY_FILE"
echo "[INFO] watcher result: $WATCHER_FILE"

echo "[DONE] Day 15 hourly compare snapshot completed"
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) END DAY15 HOURLY ==="
exit 0
