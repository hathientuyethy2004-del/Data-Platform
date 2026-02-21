#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT_DIR"

TMP_DIR="/tmp/day10_sim_go_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$TMP_DIR"

DAY9_FILE="documentation/migration/reports/DAY9_STABILITY_REPORT.json"
CHECKLIST_FILE="documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md"
ACTIVE_FILE="infrastructure/docker/migration-day4/.env.day10.active"

cp "$DAY9_FILE" "$TMP_DIR/day9.json.bak"
cp "$CHECKLIST_FILE" "$TMP_DIR/checklist.md.bak"
if [[ -f "$ACTIVE_FILE" ]]; then
  cp "$ACTIVE_FILE" "$TMP_DIR/day10.active.bak"
  ACTIVE_EXISTED=1
else
  ACTIVE_EXISTED=0
fi

python - <<'PY'
import json
from pathlib import Path
p = Path('documentation/migration/reports/DAY9_STABILITY_REPORT.json')
data = json.loads(p.read_text(encoding='utf-8'))
data.setdefault('summary', {})['status'] = 'GO'
data['summary']['ready_for_day10_canary_20'] = True
data['summary']['blockers'] = []
p.write_text(json.dumps(data, indent=2), encoding='utf-8')
print('[SIM] DAY9 status forced to GO')
PY

bash infrastructure/docker/migration-day4/scripts/run_day10_rollout_guarded.sh

python - <<'PY'
import json
from pathlib import Path
root = Path('.')
rollout = json.loads((root/'documentation/migration/reports/DAY10_ROLLOUT_REPORT.json').read_text(encoding='utf-8'))
watcher = json.loads((root/'documentation/migration/reports/DAY10_WATCHER_RESULT.json').read_text(encoding='utf-8'))
checklist = (root/'documentation/migration/MIGRATION_CHECKLIST_30_DAYS.md').read_text(encoding='utf-8')
active_exists = (root/'infrastructure/docker/migration-day4/.env.day10.active').exists()
line = next((ln for ln in checklist.splitlines() if 'Tăng canary lên 20% nếu error rate và mismatch trong ngưỡng.' in ln), 'NOT_FOUND')
print('[VERIFY] rollout_status=', rollout.get('summary', {}).get('status'))
print('[VERIFY] rollout_applied=', rollout.get('rollout', {}).get('applied'))
print('[VERIFY] effective_percent=', rollout.get('rollout', {}).get('effective_percent'))
print('[VERIFY] watcher_checklist_updated=', watcher.get('checklist_updated'))
print('[VERIFY] checklist_line=', line)
print('[VERIFY] active_env_exists=', active_exists)
PY

cp documentation/migration/reports/DAY10_ROLLOUT_REPORT.json documentation/migration/reports/DAY10_ROLLOUT_REPORT_SIMULATED_GO.json
cp documentation/migration/reports/DAY10_WATCHER_RESULT.json documentation/migration/reports/DAY10_WATCHER_RESULT_SIMULATED_GO.json

echo "[SIM] Saved simulation artifacts:"
echo "  - documentation/migration/reports/DAY10_ROLLOUT_REPORT_SIMULATED_GO.json"
echo "  - documentation/migration/reports/DAY10_WATCHER_RESULT_SIMULATED_GO.json"

cp "$TMP_DIR/day9.json.bak" "$DAY9_FILE"
cp "$TMP_DIR/checklist.md.bak" "$CHECKLIST_FILE"
if [[ "$ACTIVE_EXISTED" -eq 1 ]]; then
  cp "$TMP_DIR/day10.active.bak" "$ACTIVE_FILE"
else
  rm -f "$ACTIVE_FILE"
fi

echo "[SIM] Restored original Day9/checklist/active-env state"
