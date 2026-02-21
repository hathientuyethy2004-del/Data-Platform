#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY16_OBSERVATION_REPORT.json"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day16_observation_runner \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  READY="$(jq -r '.summary.ready_for_day17_read_switch // false' "$OUT_FILE")"
  BLOCKERS="$(jq -r '.summary.blockers | join(",")' "$OUT_FILE")"
  echo "[INFO] day16_status=$STATUS ready_for_day17=$READY blockers=${BLOCKERS:-none}"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 16 observation passed"
else
  echo "[WARN] Day 16 observation not ready yet"
fi

exit 0
