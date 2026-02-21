#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY9_STABILITY_REPORT.json"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day9_readiness_runner \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  BLOCKERS="$(jq -r '.summary.blockers | join(",")' "$OUT_FILE")"
  echo "[INFO] day9_status=$STATUS blockers=${BLOCKERS:-none}"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 9 GO for Day 10 canary 20%"
else
  echo "[WARN] Day 9 NO_GO (expected until blockers are cleared)"
fi

exit 0
