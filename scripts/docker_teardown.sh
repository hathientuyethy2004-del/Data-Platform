#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="infrastructure/docker/platform/docker-compose.yml"
DOCKER_PROFILE="${DOCKER_PROFILE:-prod}"
REMOVE_VOLUMES="${REMOVE_VOLUMES:-0}"

echo "[STEP] Tearing down Docker stack (profile=$DOCKER_PROFILE)"
if [[ "$REMOVE_VOLUMES" == "1" ]]; then
  docker compose --profile "$DOCKER_PROFILE" -f "$COMPOSE_FILE" down -v --remove-orphans
else
  docker compose --profile "$DOCKER_PROFILE" -f "$COMPOSE_FILE" down --remove-orphans
fi

echo "[DONE] Docker stack stopped"
