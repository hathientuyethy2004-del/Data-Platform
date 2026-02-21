#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY12_ALERT_VALIDATION_REPORT.json"
SAMPLE_FILE="documentation/migration/reports/DAY12_ALERT_OBSERVATIONS_SAMPLE.json"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day12_post_tuning_validator \
  --sample-output "$SAMPLE_FILE" \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  REDUCE="$(jq -r '.comparison.false_positive_rate_reduction_pct_points // "n/a"' "$OUT_FILE")"
  FN="$(jq -r '.comparison.after_policy.evaluation.false_negative_incident_windows // "n/a"' "$OUT_FILE")"
  echo "[INFO] day12_status=$STATUS fp_reduction_pp=$REDUCE false_negative_windows=$FN"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 12 post-tuning validation passed"
else
  echo "[WARN] Day 12 validation needs further tuning"
fi

exit 0
