#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY22_24_CUTOVER_REPORT.json"
ENV_FILE="infrastructure/docker/migration-day4/.env.day22_24.cutover100.example"
WATCHER_FILE="documentation/migration/reports/DAY22_24_WATCHER_RESULT.json"
ACTIVE_ENV_FILE="infrastructure/docker/migration-day4/.env.day22_24.active"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day22_24_cutover_runner \
  --env-file "$ENV_FILE" \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

PYTHONPATH=. python -m shared.platform.migration_templates.day22_24_cutover_watcher \
  --report "$OUT_FILE" \
  --checklist documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md \
  --output "$WATCHER_FILE"

APPLIED="false"
if command -v jq >/dev/null 2>&1; then
  APPLIED="$(jq -r '.cutover.applied // false' "$OUT_FILE")"
else
  APPLIED="$(python - <<'PY'
import json
from pathlib import Path
report = json.loads(Path('documentation/migration/reports/DAY22_24_CUTOVER_REPORT.json').read_text())
print(str(report.get('cutover', {}).get('applied', False)).lower())
PY
)"
fi

if [[ "$APPLIED" == "true" ]]; then
  cp "$ENV_FILE" "$ACTIVE_ENV_FILE"
  echo "[DONE] Applied Day22-24 profile to $ACTIVE_ENV_FILE"
fi

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  EFF="$(jq -r '.cutover.effective_write_load_percent // "n/a"' "$OUT_FILE")"
  SHADOW="$(jq -r '.cutover.shadow_read_legacy_enabled // false' "$OUT_FILE")"
  WINDOW="$(jq -r '.cutover.shadow_read_window_days // "n/a"' "$OUT_FILE")"
  MON="$(jq -r '.monitoring.overall_status // "UNKNOWN"' "$OUT_FILE")"
  BLK="$(jq -r '.cutover.blockers | join(",")' "$OUT_FILE")"
  echo "[INFO] day22_24_status=$STATUS cutover_applied=$APPLIED effective_write_load=$EFF shadow_read=$SHADOW shadow_window_days=$WINDOW monitoring=$MON blockers=${BLK:-none}"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day22-24 cutover applied"
else
  echo "[WARN] Day22-24 cutover blocked by guardrails"
fi

echo "[INFO] watcher report: $WATCHER_FILE"

exit 0
