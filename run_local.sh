#!/usr/bin/env bash
# Corre el panel sintético con modelo local MLX (sin API key, sin costo).
# Requiere que start_servidor_local.sh esté corriendo en otra terminal.
set -e
cd "$(dirname "$0")"

MODEL="${1:-mlx-community/Qwen2.5-7B-Instruct-4bit}"
# Nombre corto para el slug del archivo de salida
MODEL_SLUG="qwen25_7b_4bit"

MONTHS=("2026_01" "2026_02" "2026_03" "2026_04" "2026_05")
mkdir -p resultados_local

for MONTH in "${MONTHS[@]}"; do
  echo ">>> Local / $MONTH"
  python3 arnes_anclaje.py \
    --model "$MODEL_SLUG" \
    --context "context_pack_${MONTH}.json" \
    --out resultados_local \
    --runs 1 \
    --max-personas 850 \
    --provider local \
    --local-url "http://127.0.0.1:8080/v1"
done

echo "=== LOCAL COMPLETO ==="
