#!/bin/sh
# Rotate the Redis password secret and restart deployments so new password is picked up.
# Usage: ./rotate_redis_secret.sh NEW_PASSWORD
set -e
if [ -z "$1" ]; then
  echo "Usage: $0 NEW_PASSWORD"
  exit 1
fi
NEW_PASS="$1"
# Update the Kubernetes secret (client-side dry-run -> apply)
kubectl create secret generic data-platform-redis-secret --from-literal=REDIS_PASSWORD="$NEW_PASS" --dry-run=client -o yaml | kubectl apply -f -
# Restart deployments so pods pick up the new secret
kubectl rollout restart deployment/data-platform-redis
kubectl rollout restart deployment/data-platform-serving
echo "Rotated secret and restarted deployments."
