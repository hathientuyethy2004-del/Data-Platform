#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="infrastructure/docker/migration-day4/.env.day8.canary10.example"
OUT_FILE="documentation/migration/reports/DAY8_CANARY_STATUS.json"

PYTHONPATH=. python -m shared.platform.migration_templates.day8_canary_runner \
  --env-file "$ENV_FILE" \
  --output "$OUT_FILE"

if command -v jq >/dev/null 2>&1; then
  STATUS="$(jq -r '.summary.status // "UNKNOWN"' "$OUT_FILE")"
  PCT="$(jq -r '.config.oss_canary_write_percent // "n/a"' "$OUT_FILE")"
  READ_LEGACY="$(jq -r '.checks.read_path_stays_legacy.status // "n/a"' "$OUT_FILE")"
  echo "[INFO] day8_status=$STATUS canary_percent=$PCT read_path_legacy_check=$READ_LEGACY"
fi

exit 0
