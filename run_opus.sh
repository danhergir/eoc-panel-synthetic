#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
source ~/.zshrc 2>/dev/null || true

MONTHS=("2026_02" "2026_03" "2026_04" "2026_05")
mkdir -p resultados_opus

for MONTH in "${MONTHS[@]}"; do
  echo ">>> Opus / $MONTH"
  python3 arnes_anclaje.py \
    --model claude-opus-4-8 \
    --context "context_pack_${MONTH}.json" \
    --out resultados_opus \
    --runs 1 \
    --max-personas 850
done

echo "=== OPUS COMPLETO ==="
