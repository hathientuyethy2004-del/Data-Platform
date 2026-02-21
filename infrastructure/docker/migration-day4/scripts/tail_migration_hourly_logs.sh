#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

FALLBACK_LINES="${1:-25}"
if ! [[ "$FALLBACK_LINES" =~ ^[0-9]+$ ]]; then
  echo "[ERROR] fallback_lines must be an integer"
  echo "Usage: bash infrastructure/docker/migration-day4/scripts/tail_migration_hourly_logs.sh [fallback_lines]"
  exit 2
fi

extract_latest_block() {
  local log_file="$1"
  local start_marker="$2"
  local end_marker="$3"

  awk -v start="$start_marker" -v end="$end_marker" '
    $0 ~ start {
      capture = 1
      block = $0 ORS
      next
    }
    capture {
      block = block $0 ORS
    }
    $0 ~ end && capture {
      last = block
      capture = 0
      block = ""
    }
    END {
      if (capture) {
        last = block
      }
      if (length(last) > 0) {
        printf "%s", last
      }
    }
  ' "$log_file"
}

show_log() {
  local title="$1"
  local log_file="$2"
  local start_marker="$3"
  local end_marker="$4"

  echo "===== ${title} ====="

  if [[ ! -f "$log_file" ]]; then
    echo "[WARN] missing log: $log_file"
    echo
    return
  fi

  local block
  block="$(extract_latest_block "$log_file" "$start_marker" "$end_marker")"

  if [[ -n "$block" ]]; then
    printf "%s\n" "$block"
  else
    echo "[WARN] no START/END block found, fallback tail -n $FALLBACK_LINES"
    tail -n "$FALLBACK_LINES" "$log_file"
    echo
  fi
}

show_log \
  "DAY14 latest block" \
  "documentation/migration/reports/DAY14_GATE2_CRON.log" \
  "=== .* START DAY14 HOURLY ===" \
  "=== .* END DAY14 HOURLY ==="

show_log \
  "DAY15 latest block" \
  "documentation/migration/reports/DAY15_COMPARE_CRON.log" \
  "=== .* START DAY15 HOURLY ===" \
  "=== .* END DAY15 HOURLY ==="

show_log \
  "DAY16 latest block" \
  "documentation/migration/reports/DAY16_OBSERVATION_CRON.log" \
  "=== .* START DAY16 HOURLY ===" \
  "=== .* END DAY16 HOURLY ==="

exit 0
