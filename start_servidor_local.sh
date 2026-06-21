#!/usr/bin/env bash
# Descarga (primera vez) e inicia el servidor local MLX compatible con OpenAI.
# Requiere: pip install mlx-lm
# Primera ejecución descarga ~4.5 GB del modelo.

MODEL="${1:-mlx-community/Qwen2.5-7B-Instruct-4bit}"
PORT="${2:-8080}"

echo "Iniciando servidor MLX con modelo: $MODEL"
echo "Endpoint: http://127.0.0.1:${PORT}/v1"
echo "(primera ejecución descarga el modelo — puede tardar varios minutos)"
echo ""

python3 -m mlx_lm.server --model "$MODEL" --port "$PORT"
