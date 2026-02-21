#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY10_ROLLOUT_REPORT.json"
ENV_FILE="infrastructure/docker/migration-day4/.env.day10.canary20.example"
WATCHER_FILE="documentation/migration/reports/DAY10_WATCHER_RESULT.json"
ACTIVE_ENV_FILE="infrastructure/docker/migration-day4/.env.day10.active"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day10_rollout_runner \
  --env-file "$ENV_FILE" \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

PYTHONPATH=. python -m shared.platform.migration_templates.day10_rollout_watcher \
  --rollout-report "$OUT_FILE" \
  --checklist documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md \
  --output "$WATCHER_FILE"

APPLIED="false"
if command -v jq >/dev/null 2>&1; then
  APPLIED="$(jq -r '.rollout.applied // false' "$OUT_FILE")"
else
  APPLIED="$(python - <<'PY'
import json
from pathlib import Path
report = json.loads(Path('documentation/migration/reports/DAY10_ROLLOUT_REPORT.json').read_text())
print(str(report.get('rollout', {}).get('applied', False)).lower())
PY
)"
fi

if [[ "$APPLIED" == "true" ]]; then
  cp "$ENV_FILE" "$ACTIVE_ENV_FILE"
  echo "[DONE] Applied Day 10 canary profile to $ACTIVE_ENV_FILE"
fi

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  EFF="$(jq -r '.rollout.effective_percent // "n/a"' "$OUT_FILE")"
  LOAD="$(jq -r '.load_backpressure.overall_status // "UNKNOWN"' "$OUT_FILE")"
  echo "[INFO] day10_status=$STATUS rollout_applied=$APPLIED effective_percent=$EFF load_test=$LOAD"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 10 rollout applied to 20%"
else
  echo "[WARN] Day 10 rollout blocked by guardrails (expected if Day 9 is NO_GO)"
fi

echo "[INFO] watcher report: $WATCHER_FILE"

exit 0
