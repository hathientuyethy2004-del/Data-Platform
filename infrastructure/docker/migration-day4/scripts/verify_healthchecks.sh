#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.staging.yml"

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] docker not found"
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "[ERROR] docker compose not found"
  exit 1
fi

echo "[INFO] Checking container states..."
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" ps

check_url() {
  local name="$1"
  local url="$2"
  if curl -fsS "$url" >/dev/null; then
    echo "[OK] $name: $url"
  else
    echo "[FAIL] $name: $url"
    return 1
  fi
}

check_tcp() {
  local name="$1"
  local host="$2"
  local port="$3"
  if bash -lc "</dev/tcp/$host/$port" 2>/dev/null; then
    echo "[OK] $name: $host:$port"
  else
    echo "[FAIL] $name: $host:$port"
    return 1
  fi
}

echo "[INFO] Running endpoint/TCP checks..."
check_url "Airflow" "http://localhost:8080/health"
check_url "Prometheus" "http://localhost:9090/-/healthy"
check_tcp "Kafka" "localhost" "9092"
check_tcp "Redis" "localhost" "6379"

echo "[DONE] All healthchecks passed"
