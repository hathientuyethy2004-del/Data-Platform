#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

export DUAL_RUN_ENABLED="${DUAL_RUN_ENABLED:-true}"
export DUAL_RUN_COMPARE_ENABLED="${DUAL_RUN_COMPARE_ENABLED:-true}"
export READ_FROM_OSS_SERVING="${READ_FROM_OSS_SERVING:-false}"

python -m shared.platform.migration_templates.day5_smoke_runner \
  --smoke-output documentation/migration/reports/DAY5_SMOKE_RESULT.json \
  --baseline-output documentation/migration/reports/BASELINE_COMPARE_REPORT_DAY5.json
