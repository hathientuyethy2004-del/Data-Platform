#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY29_DECOMMISSION_REPORT.json"
ENV_FILE="infrastructure/docker/migration-day4/.env.day29.decommission.example"
WATCHER_FILE="documentation/migration/reports/DAY29_WATCHER_RESULT.json"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day29_decommission_runner \
  --env-file "$ENV_FILE" \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

PYTHONPATH=. python -m shared.platform.migration_templates.day29_decommission_watcher \
  --report "$OUT_FILE" \
  --checklist documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md \
  --output "$WATCHER_FILE"

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  CRON="$(jq -r '.checks.legacy_cron_removed.status // "FAIL"' "$OUT_FILE")"
  JOBS="$(jq -r '.checks.legacy_jobs_disabled.status // "FAIL"' "$OUT_FILE")"
  ROUTES="$(jq -r '.checks.legacy_routes_disabled.status // "FAIL"' "$OUT_FILE")"
  CONFIGS="$(jq -r '.checks.legacy_configs_archived.status // "FAIL"' "$OUT_FILE")"
  BACKUP="$(jq -r '.checks.backup_config_done.status // "FAIL"' "$OUT_FILE")"
  RUNBOOK="$(jq -r '.checks.runbook_finalized.status // "FAIL"' "$OUT_FILE")"
  SNAPSHOT="$(jq -r '.checks.rollback_snapshot_created.status // "FAIL"' "$OUT_FILE")"
  DRYRUN="$(jq -r '.checks.decommission_dry_run_pass.status // "FAIL"' "$OUT_FILE")"
  BLK="$(jq -r '.decommission.blockers | join(",")' "$OUT_FILE")"
  echo "[INFO] day29_status=$STATUS cron_removed=$CRON jobs_disabled=$JOBS routes_disabled=$ROUTES configs_archived=$CONFIGS backup_done=$BACKUP runbook_finalized=$RUNBOOK rollback_snapshot=$SNAPSHOT dry_run=$DRYRUN blockers=${BLK:-none}"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 29 decommission checks passed"
else
  echo "[WARN] Day 29 decommission checks blocked by guardrails"
fi

echo "[INFO] watcher report: $WATCHER_FILE"

exit 0
