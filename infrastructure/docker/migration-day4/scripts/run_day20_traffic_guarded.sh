#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY20_TRAFFIC_REPORT.json"
ENV_FILE="infrastructure/docker/migration-day4/.env.day20.traffic80.example"
WATCHER_FILE="documentation/migration/reports/DAY20_WATCHER_RESULT.json"
ACTIVE_ENV_FILE="infrastructure/docker/migration-day4/.env.day20.active"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day20_traffic_runner \
  --env-file "$ENV_FILE" \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

PYTHONPATH=. python -m shared.platform.migration_templates.day20_traffic_watcher \
  --report "$OUT_FILE" \
  --checklist documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md \
  --output "$WATCHER_FILE"

APPLIED="false"
if command -v jq >/dev/null 2>&1; then
  APPLIED="$(jq -r '.traffic.applied // false' "$OUT_FILE")"
else
  APPLIED="$(python - <<'PY'
import json
from pathlib import Path
report = json.loads(Path('documentation/migration/reports/DAY20_TRAFFIC_REPORT.json').read_text())
print(str(report.get('traffic', {}).get('applied', False)).lower())
PY
)"
fi

if [[ "$APPLIED" == "true" ]]; then
  cp "$ENV_FILE" "$ACTIVE_ENV_FILE"
  echo "[DONE] Applied Day 20 traffic profile to $ACTIVE_ENV_FILE"
fi

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  EFF="$(jq -r '.traffic.effective_total_percent // "n/a"' "$OUT_FILE")"
  MON="$(jq -r '.monitoring.overall_status // "UNKNOWN"' "$OUT_FILE")"
  BLK="$(jq -r '.traffic.blockers | join(",")' "$OUT_FILE")"
  echo "[INFO] day20_status=$STATUS traffic_applied=$APPLIED effective_total_percent=$EFF monitoring=$MON blockers=${BLK:-none}"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 20 traffic increased to 80%"
else
  echo "[WARN] Day 20 traffic increase blocked by guardrails"
fi

echo "[INFO] watcher report: $WATCHER_FILE"

exit 0
