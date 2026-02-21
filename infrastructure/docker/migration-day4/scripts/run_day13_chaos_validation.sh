#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY13_CHAOS_REPORT.json"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day13_chaos_runner \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  PASS_CNT="$(jq -r '.summary.scenarios_passed // 0' "$OUT_FILE")"
  TOTAL_CNT="$(jq -r '.summary.scenarios_total // 0' "$OUT_FILE")"
  INTEGRITY="$(jq -r '.summary.integrity_passed // false' "$OUT_FILE")"
  echo "[INFO] day13_status=$STATUS scenarios=$PASS_CNT/$TOTAL_CNT integrity=$INTEGRITY"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 13 chaos validation passed"
else
  echo "[WARN] Day 13 chaos validation failed"
fi

exit 0
