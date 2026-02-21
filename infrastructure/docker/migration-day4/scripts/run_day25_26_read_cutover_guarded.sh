#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY25_26_READ_CUTOVER_REPORT.json"
ENV_FILE="infrastructure/docker/migration-day4/.env.day25_26.read100.example"
WATCHER_FILE="documentation/migration/reports/DAY25_26_WATCHER_RESULT.json"
ACTIVE_ENV_FILE="infrastructure/docker/migration-day4/.env.day25_26.active"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day25_26_read_cutover_runner \
  --env-file "$ENV_FILE" \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

PYTHONPATH=. python -m shared.platform.migration_templates.day25_26_read_cutover_watcher \
  --report "$OUT_FILE" \
  --checklist documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md \
  --output "$WATCHER_FILE"

APPLIED="false"
if command -v jq >/dev/null 2>&1; then
  APPLIED="$(jq -r '.read_cutover.applied // false' "$OUT_FILE")"
else
  APPLIED="$(python - <<'PY'
import json
from pathlib import Path
report = json.loads(Path('documentation/migration/reports/DAY25_26_READ_CUTOVER_REPORT.json').read_text())
print(str(report.get('read_cutover', {}).get('applied', False)).lower())
PY
)"
fi

if [[ "$APPLIED" == "true" ]]; then
  cp "$ENV_FILE" "$ACTIVE_ENV_FILE"
  echo "[DONE] Applied Day25-26 profile to $ACTIVE_ENV_FILE"
fi

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  EFF="$(jq -r '.read_cutover.effective_read_switch_percent // "n/a"' "$OUT_FILE")"
  LEGACY_JOBS="$(jq -r '.read_cutover.legacy_jobs_disabled // false' "$OUT_FILE")"
  LEGACY_ROUTES="$(jq -r '.read_cutover.legacy_routes_disabled // false' "$OUT_FILE")"
  LEGACY_CFG="$(jq -r '.read_cutover.legacy_configs_archived // false' "$OUT_FILE")"
  MON="$(jq -r '.monitoring.overall_status // "UNKNOWN"' "$OUT_FILE")"
  BLK="$(jq -r '.read_cutover.blockers | join(",")' "$OUT_FILE")"
  echo "[INFO] day25_26_status=$STATUS read_cutover_applied=$APPLIED effective_read_percent=$EFF legacy_jobs_disabled=$LEGACY_JOBS legacy_routes_disabled=$LEGACY_ROUTES legacy_configs_archived=$LEGACY_CFG monitoring=$MON blockers=${BLK:-none}"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day25-26 read cutover applied"
else
  echo "[WARN] Day25-26 read cutover blocked by guardrails"
fi

echo "[INFO] watcher report: $WATCHER_FILE"

exit 0
