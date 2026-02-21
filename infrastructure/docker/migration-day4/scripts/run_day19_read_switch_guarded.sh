#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY19_READ_SWITCH_REPORT.json"
ENV_FILE="infrastructure/docker/migration-day4/.env.day19.read50.example"
WATCHER_FILE="documentation/migration/reports/DAY19_WATCHER_RESULT.json"
ACTIVE_ENV_FILE="infrastructure/docker/migration-day4/.env.day19.active"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day19_read_switch_runner \
  --env-file "$ENV_FILE" \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

PYTHONPATH=. python -m shared.platform.migration_templates.day19_read_switch_watcher \
  --report "$OUT_FILE" \
  --checklist documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md \
  --output "$WATCHER_FILE"

APPLIED="false"
if command -v jq >/dev/null 2>&1; then
  APPLIED="$(jq -r '.read_switch.applied // false' "$OUT_FILE")"
else
  APPLIED="$(python - <<'PY'
import json
from pathlib import Path
report = json.loads(Path('documentation/migration/reports/DAY19_READ_SWITCH_REPORT.json').read_text())
print(str(report.get('read_switch', {}).get('applied', False)).lower())
PY
)"
fi

if [[ "$APPLIED" == "true" ]]; then
  cp "$ENV_FILE" "$ACTIVE_ENV_FILE"
  echo "[DONE] Applied Day 19 read switch profile to $ACTIVE_ENV_FILE"
fi

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  EFF="$(jq -r '.read_switch.effective_percent // "n/a"' "$OUT_FILE")"
  MON="$(jq -r '.monitoring.overall_status // "UNKNOWN"' "$OUT_FILE")"
  BLK="$(jq -r '.read_switch.blockers | join(",")' "$OUT_FILE")"
  echo "[INFO] day19_status=$STATUS read_switch_applied=$APPLIED effective_percent=$EFF monitoring=$MON blockers=${BLK:-none}"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 19 read switch applied to 50%"
else
  echo "[WARN] Day 19 read switch blocked by guardrails"
fi

echo "[INFO] watcher report: $WATCHER_FILE"

exit 0
