#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

OUT_FILE="documentation/migration/reports/DAY30_CLOSURE_REPORT.json"
ENV_FILE="infrastructure/docker/migration-day4/.env.day30.closure.example"
WATCHER_FILE="documentation/migration/reports/DAY30_WATCHER_RESULT.json"

set +e
PYTHONPATH=. python -m shared.platform.migration_templates.day30_closure_runner \
  --env-file "$ENV_FILE" \
  --output "$OUT_FILE"
RUN_CODE=$?
set -e

PYTHONPATH=. python -m shared.platform.migration_templates.day30_closure_watcher \
  --report "$OUT_FILE" \
  --checklist documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md \
  --output "$WATCHER_FILE"

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  DEP="$(jq -r '.checks.day29_decommission_required.status // "FAIL"' "$OUT_FILE")"
  ACCEPT="$(jq -r '.checks.technical_acceptance_signed.status // "FAIL"' "$OUT_FILE")"
  LESSONS="$(jq -r '.checks.lessons_learned_published.status // "FAIL"' "$OUT_FILE")"
  OPTI="$(jq -r '.checks.optimization_phase_kickoff.status // "FAIL"' "$OUT_FILE")"
  BLK="$(jq -r '.closure.blockers | join(",")' "$OUT_FILE")"
  echo "[INFO] day30_status=$STATUS day29_dependency=$DEP technical_acceptance=$ACCEPT lessons_learned=$LESSONS optimization_kickoff=$OPTI blockers=${BLK:-none}"
fi

if [[ "$RUN_CODE" -eq 0 ]]; then
  echo "[DONE] Day 30 closure checks passed"
else
  echo "[WARN] Day 30 closure checks blocked by guardrails"
fi

echo "[INFO] watcher report: $WATCHER_FILE"

exit 0
