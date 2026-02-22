#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "=== [1/2] Shared tests ==="
PYTHONPATH=. pytest -q shared/tests

echo ""
echo "=== [2/2] Product tests ==="
PRODUCTS=(
  "web-user-analytics"
  "operational-metrics"
  "compliance-auditing"
  "user-segmentation"
  "mobile-user-analytics"
)

for product in "${PRODUCTS[@]}"; do
  echo ""
  echo "=== pytest product: ${product} ==="
  (
    cd "products/${product}"
    PYTHONPATH=. pytest -q src/tests
  )
done

echo ""
echo "Pre-merge regression suite completed successfully."