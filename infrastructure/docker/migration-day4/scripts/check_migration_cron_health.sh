#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

WINDOW_MINUTES="60"
JSON_OUTPUT=""
FLAT_OUTPUT=""

usage() {
  echo "Usage: bash infrastructure/docker/migration-day4/scripts/check_migration_cron_health.sh [window_minutes] [--window-minutes N] [--json-output PATH] [--flat-output PATH]"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --window-minutes)
      WINDOW_MINUTES="${2:-}"
      shift 2
      ;;
    --json-output)
      JSON_OUTPUT="${2:-}"
      shift 2
      ;;
    --flat-output)
      FLAT_OUTPUT="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "${POSITIONAL_WINDOW_SET:-}" && "$1" =~ ^[0-9]+$ ]]; then
        WINDOW_MINUTES="$1"
        POSITIONAL_WINDOW_SET=1
        shift
      else
        echo "[ERROR] unknown argument: $1"
        usage
        exit 2
      fi
      ;;
  esac
done

if ! [[ "$WINDOW_MINUTES" =~ ^[0-9]+$ ]]; then
  echo "[ERROR] window_minutes must be an integer"
  usage
  exit 2
fi

WINDOW_SECONDS=$((WINDOW_MINUTES * 60))
NOW_EPOCH="$(date -u +%s)"

declare -a CHECK_KEYS=(
  "day14_gate2_hourly"
  "day15_compare_hourly"
  "day27_validation_hourly"
  "day28_freeze_hourly"
  "day29_decommission_hourly"
  "day30_closure_hourly"
)

declare -A LOG_FILE_BY_KEY=(
  ["day14_gate2_hourly"]="documentation/migration/reports/DAY14_GATE2_CRON.log"
  ["day15_compare_hourly"]="documentation/migration/reports/DAY15_COMPARE_CRON.log"
  ["day27_validation_hourly"]="documentation/migration/reports/DAY27_VALIDATION_CRON.log"
  ["day28_freeze_hourly"]="documentation/migration/reports/DAY28_FREEZE_CRON.log"
  ["day29_decommission_hourly"]="documentation/migration/reports/DAY29_DECOMMISSION_CRON.log"
  ["day30_closure_hourly"]="documentation/migration/reports/DAY30_CLOSURE_CRON.log"
)

declare -A CHECK_STATUS
declare -A CHECK_EXISTS
declare -A CHECK_AGE_SECONDS

for key in "${CHECK_KEYS[@]}"; do
  CHECK_STATUS["$key"]="FAIL"
  CHECK_EXISTS["$key"]="false"
  CHECK_AGE_SECONDS["$key"]="-1"
done

check_log_freshness() {
  local label="$1"
  local log_file="${LOG_FILE_BY_KEY[$label]}"

  if [[ ! -f "$log_file" ]]; then
    CHECK_EXISTS["$label"]="false"
    CHECK_STATUS["$label"]="FAIL"
    CHECK_AGE_SECONDS["$label"]="-1"
    echo "[FAIL] $label missing log file: $log_file"
    return 1
  fi

  CHECK_EXISTS["$label"]="true"

  local mtime
  mtime="$(stat -c %Y "$log_file")"
  local age=$((NOW_EPOCH - mtime))
  CHECK_AGE_SECONDS["$label"]="$age"

  if (( age <= WINDOW_SECONDS )); then
    CHECK_STATUS["$label"]="PASS"
    echo "[PASS] $label updated ${age}s ago (<= ${WINDOW_SECONDS}s)"
    return 0
  fi

  CHECK_STATUS["$label"]="FAIL"
  echo "[FAIL] $label stale: ${age}s ago (> ${WINDOW_SECONDS}s)"
  return 1
}

status=0
for key in "${CHECK_KEYS[@]}"; do
  check_log_freshness "$key" || status=1
done

OVERALL_STATUS="FAIL"
if [[ "$status" -eq 0 ]]; then
  OVERALL_STATUS="PASS"
fi

if [[ -n "$JSON_OUTPUT" ]]; then
  mkdir -p "$(dirname "$JSON_OUTPUT")"

  checks_json=""
  for key in "${CHECK_KEYS[@]}"; do
    if [[ -n "$checks_json" ]]; then
      checks_json+=$',\n'
    fi
    checks_json+="    \"${key}\": {"
    checks_json+=$'\n'
    checks_json+="      \"status\": \"${CHECK_STATUS[$key]}\","
    checks_json+=$'\n'
    checks_json+="      \"log_file\": \"${LOG_FILE_BY_KEY[$key]}\","
    checks_json+=$'\n'
    checks_json+="      \"exists\": ${CHECK_EXISTS[$key]},"
    checks_json+=$'\n'
    checks_json+="      \"age_seconds\": ${CHECK_AGE_SECONDS[$key]}"
    checks_json+=$'\n'
    checks_json+="    }"
  done

  cat > "$JSON_OUTPUT" <<EOF
{
  "run_ts": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "window_minutes": $WINDOW_MINUTES,
  "window_seconds": $WINDOW_SECONDS,
  "status": "$OVERALL_STATUS",
  "checks": {
${checks_json}
  }
}
EOF
  echo "[INFO] wrote_json_status=$JSON_OUTPUT"
fi

if [[ -n "$FLAT_OUTPUT" ]]; then
  mkdir -p "$(dirname "$FLAT_OUTPUT")"
  printf '{"panel_id":"migration_cron_health_quick_panel","run_ts":"%s","overall_status":"%s","window_minutes":%s,"day14_status":"%s","day14_age_seconds":%s,"day14_log_exists":%s,"day15_status":"%s","day15_age_seconds":%s,"day15_log_exists":%s,"day27_status":"%s","day27_age_seconds":%s,"day27_log_exists":%s,"day28_status":"%s","day28_age_seconds":%s,"day28_log_exists":%s,"day29_status":"%s","day29_age_seconds":%s,"day29_log_exists":%s,"day30_status":"%s","day30_age_seconds":%s,"day30_log_exists":%s}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "$OVERALL_STATUS" \
    "$WINDOW_MINUTES" \
    "${CHECK_STATUS[day14_gate2_hourly]}" \
    "${CHECK_AGE_SECONDS[day14_gate2_hourly]}" \
    "${CHECK_EXISTS[day14_gate2_hourly]}" \
    "${CHECK_STATUS[day15_compare_hourly]}" \
    "${CHECK_AGE_SECONDS[day15_compare_hourly]}" \
    "${CHECK_EXISTS[day15_compare_hourly]}" \
    "${CHECK_STATUS[day27_validation_hourly]}" \
    "${CHECK_AGE_SECONDS[day27_validation_hourly]}" \
    "${CHECK_EXISTS[day27_validation_hourly]}" \
    "${CHECK_STATUS[day28_freeze_hourly]}" \
    "${CHECK_AGE_SECONDS[day28_freeze_hourly]}" \
    "${CHECK_EXISTS[day28_freeze_hourly]}" \
    "${CHECK_STATUS[day29_decommission_hourly]}" \
    "${CHECK_AGE_SECONDS[day29_decommission_hourly]}" \
    "${CHECK_EXISTS[day29_decommission_hourly]}" \
    "${CHECK_STATUS[day30_closure_hourly]}" \
    "${CHECK_AGE_SECONDS[day30_closure_hourly]}" \
    "${CHECK_EXISTS[day30_closure_hourly]}" > "$FLAT_OUTPUT"
  echo "[INFO] wrote_flat_status=$FLAT_OUTPUT"
fi

if [[ "$status" -eq 0 ]]; then
  echo "[DONE] cron_health=PASS window_minutes=$WINDOW_MINUTES"
  exit 0
fi

echo "[WARN] cron_health=FAIL window_minutes=$WINDOW_MINUTES"
exit 2
