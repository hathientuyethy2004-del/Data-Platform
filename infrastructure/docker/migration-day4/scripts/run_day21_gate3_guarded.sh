#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY21_GATE3_REPORT.json"
WATCHER_FILE="documentation/migration/reports/DAY21_WATCHER_RESULT.json"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day21_gate3_runner \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

PYTHONPATH=. python -m shared.platform.migration_templates.day21_gate3_watcher \
  --gate-report "$OUT_FILE" \
  --checklist documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md \
  --output "$WATCHER_FILE"

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  BLK="$(jq -r '.summary.blockers | join(",")' "$OUT_FILE")"
  HRS="$(jq -r '.checks.traffic_80_stable_72h.observed_hours // "n/a"' "$OUT_FILE")"
  RATE="$(jq -r '.checks.compare_pass_rate_99_5.compare_pass_rate_pct // "n/a"' "$OUT_FILE")"
  echo "[INFO] day21_status=$STATUS observed_hours=$HRS compare_pass_rate_pct=$RATE blockers=${BLK:-none}"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 21 Gate 3 passed"
else
  echo "[WARN] Day 21 Gate 3 not met yet"
fi

echo "[INFO] watcher report: $WATCHER_FILE"

exit 0
