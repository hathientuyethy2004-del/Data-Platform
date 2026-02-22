#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="infrastructure/docker/platform/docker-compose.yml"
DOCKER_PROFILE="${DOCKER_PROFILE:-prod}"
API_PORT="${API_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-8080}"
API_DEV_PORT="${API_DEV_PORT:-8001}"
FRONTEND_DEV_PORT="${FRONTEND_DEV_PORT:-5173}"

if [[ "$DOCKER_PROFILE" == "dev" ]]; then
  API_BASE="http://127.0.0.1:${API_DEV_PORT}"
  FRONTEND_BASE="http://127.0.0.1:${FRONTEND_DEV_PORT}"
else
  API_BASE="http://127.0.0.1:${API_PORT}"
  FRONTEND_BASE="http://127.0.0.1:${FRONTEND_PORT}"
fi

wait_for_url() {
  local url="$1"
  local name="$2"
  local max_attempts="${3:-60}"
  local attempt=1

  while (( attempt <= max_attempts )); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[OK] $name is ready: $url"
      return 0
    fi
    sleep 2
    ((attempt++))
  done

  echo "[ERROR] Timeout waiting for $name: $url"
  return 1
}

assert_status() {
  local method="$1"
  local path="$2"
  local expected="$3"
  local token="${4:-}"
  local body="${5:-}"
  local tmp
  tmp=$(mktemp)

  local status
  if [[ -n "$token" && -n "$body" ]]; then
    status=$(curl -sS -o "$tmp" -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -H "Authorization: Bearer $token" -d "$body" "$API_BASE$path")
  elif [[ -n "$token" ]]; then
    status=$(curl -sS -o "$tmp" -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -H "Authorization: Bearer $token" "$API_BASE$path")
  elif [[ -n "$body" ]]; then
    status=$(curl -sS -o "$tmp" -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$body" "$API_BASE$path")
  else
    status=$(curl -sS -o "$tmp" -w "%{http_code}" -X "$method" "$API_BASE$path")
  fi

  if [[ "$status" != "$expected" ]]; then
    echo "[FAIL] $method $path expected $expected got $status"
    echo "[FAIL] response: $(tr '\n' ' ' < "$tmp" | cut -c1-300)"
    rm -f "$tmp"
    return 1
  fi

  echo "[PASS] $method $path -> $status"
  rm -f "$tmp"
}

echo "[STEP] Building and starting Docker stack (profile=$DOCKER_PROFILE)"
docker compose --profile "$DOCKER_PROFILE" -f "$COMPOSE_FILE" up -d --build --remove-orphans

echo "[STEP] Waiting for services"
wait_for_url "$FRONTEND_BASE/" "frontend"
wait_for_url "$API_BASE/health" "api"

echo "[STEP] Runtime API smoke"
assert_status GET "/health" "200"
assert_status GET "/api/v1/dashboard/summary" "401"
assert_status POST "/api/v1/auth/login" "200" "" '{"token":"viewer-token"}'
assert_status GET "/api/v1/auth/session" "200" "viewer-token"
assert_status GET "/api/v1/products?page=1&page_size=5" "200" "viewer-token"
assert_status POST "/api/v1/products/web-user-analytics/tests/run" "403" "viewer-token" '{}'
assert_status POST "/api/v1/products/web-user-analytics/tests/run" "200" "operator-token" '{}'
assert_status POST "/api/v1/platform/actions/reload-config" "403" "operator-token" '{}'
assert_status POST "/api/v1/platform/actions/reload-config" "200" "admin-token" '{}'

echo "[DONE] Docker stack is up and runtime smoke checks passed"
echo "       Profile: $DOCKER_PROFILE"
echo "       Frontend: $FRONTEND_BASE"
echo "       API: $API_BASE"
