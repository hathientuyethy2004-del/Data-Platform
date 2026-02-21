#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY11_TUNING_REPORT.json"
THRESHOLD_FILE="infrastructure/docker/migration-day4/alert_thresholds.day11.tuned.json"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day11_tuning_runner \
  --output "$OUT_FILE" \
  --threshold-output "$THRESHOLD_FILE"
RUN_CODE=$?
set -e

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  CNT="$(jq -r '.summary.bottleneck_items_count // 0' "$OUT_FILE")"
  P95W="$(jq -r '.alert_tuning.tuned_thresholds.latency_p95_warning_ms // "n/a"' "$OUT_FILE")"
  ERW="$(jq -r '.alert_tuning.tuned_thresholds.error_rate_warning_pct // "n/a"' "$OUT_FILE")"
  echo "[INFO] day11_status=$STATUS bottlenecks=$CNT tuned_p95_warn_ms=$P95W tuned_error_warn_pct=$ERW"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 11 tuning completed"
else
  echo "[WARN] Day 11 tuning requires further investigation"
fi

exit 0
