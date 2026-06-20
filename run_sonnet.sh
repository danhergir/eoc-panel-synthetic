#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
source ~/.zshrc 2>/dev/null || true

MONTHS=("2025_10" "2025_12" "2026_01" "2026_02" "2026_03" "2026_04" "2026_05")
mkdir -p resultados_sonnet

for MONTH in "${MONTHS[@]}"; do
  echo ">>> Sonnet / $MONTH"
  python3 arnes_anclaje.py \
    --model claude-sonnet-4-6 \
    --context "context_pack_${MONTH}.json" \
    --out resultados_sonnet \
    --runs 1 \
    --max-personas 850
done

echo "=== SONNET COMPLETO ==="
