#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY14_GATE2_REPORT.json"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day14_gate2_runner \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  BLK="$(jq -r '.summary.blockers | join(",")' "$OUT_FILE")"
  HRS="$(jq -r '.checks.canary_20_stable_48h.observed_hours // "n/a"' "$OUT_FILE")"
  echo "[INFO] day14_status=$STATUS observed_hours=$HRS blockers=${BLK:-none}"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 14 Gate 2 passed"
else
  echo "[WARN] Day 14 Gate 2 not met yet"
fi

exit 0
