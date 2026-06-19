#!/usr/bin/env bash
# Pipeline completo EOC — ejecuta en orden correcto del §7 pre-registro
set -e

MODEL_SONNET="claude-sonnet-4-6"
MODEL_OPUS="claude-opus-4-8"

MONTHS_SONNET=("2025_10" "2025_12" "2026_01" "2026_02" "2026_03" "2026_04" "2026_05")
MONTHS_OPUS=("2026_02" "2026_03" "2026_04" "2026_05")

MAX_PERSONAS=${MAX_PERSONAS:-850}   # Override: MAX_PERSONAS=100 bash arranque.sh
RUNS=${RUNS:-1}

echo "============================================================"
echo "  Pipeline EOC — Panel Sintético Fedesarrollo"
echo "  Modo: MAX_PERSONAS=$MAX_PERSONAS  RUNS=$RUNS"
echo "============================================================"

# ── PASO 1: Sonda de memorización ──────────────────────────────
echo ""
echo "PASO 1 — Sonda de memorización"
echo "-------------------------------"

python sonda_memorizacion.py \
  --model "$MODEL_SONNET" \
  --actuals actuals_sellados.json \
  --out sonda_sonnet.json

python sonda_memorizacion.py \
  --model "$MODEL_OPUS" \
  --actuals actuals_sellados.json \
  --out sonda_opus.json

echo ""
echo "✓ Sondas completas. Revisa sonda_sonnet.json y sonda_opus.json"
echo "  para confirmar qué meses son hold-out limpios."

# ── PAUSA 1: Commit del pre-registro ───────────────────────────
echo ""
echo "============================================================"
echo "  ⏸  PAUSA OBLIGATORIA §7 — PASO 2"
echo ""
echo "  Antes de continuar, haz commit del pre-registro:"
echo ""
echo "    git add pre-registro-validacion-eoc.md sonda_sonnet.json sonda_opus.json"
echo "    git commit -m 'pre-registro: sondas completadas, hipótesis congeladas'"
echo ""
echo "  Cuando hayas hecho el commit, presiona ENTER para continuar..."
echo "============================================================"
read -r

# ── PASO 3: Arnés de anclaje ───────────────────────────────────
echo ""
echo "PASO 3 — Arnés de anclaje (generando predicciones)"
echo "----------------------------------------------------"
echo "  ⚠️  NO abrir actuals_sellados.json en este paso"
echo ""

mkdir -p resultados_sonnet resultados_opus

for MONTH in "${MONTHS_SONNET[@]}"; do
  echo "  → Sonnet / $MONTH"
  python arnes_anclaje.py \
    --model "$MODEL_SONNET" \
    --context "context_pack_${MONTH}.json" \
    --out resultados_sonnet \
    --runs "$RUNS" \
    --max-personas "$MAX_PERSONAS"
done

for MONTH in "${MONTHS_OPUS[@]}"; do
  echo "  → Opus / $MONTH"
  python arnes_anclaje.py \
    --model "$MODEL_OPUS" \
    --context "context_pack_${MONTH}.json" \
    --out resultados_opus \
    --runs "$RUNS" \
    --max-personas "$MAX_PERSONAS"
done

echo ""
echo "✓ Predicciones generadas en resultados_sonnet/ y resultados_opus/"

# ── PAUSA 2: Commit de predicciones ────────────────────────────
echo ""
echo "============================================================"
echo "  ⏸  PAUSA OBLIGATORIA §7 — PASO 4"
echo ""
echo "  Antes de ver los actuales, haz commit de las predicciones:"
echo ""
echo "    git add resultados_sonnet/ resultados_opus/"
echo "    git commit -m 'predicciones: panel sintético generado, antes de abrir actuales'"
echo ""
echo "  Cuando hayas hecho el commit, presiona ENTER para continuar..."
echo "============================================================"
read -r

# ── PASO 5: Puntuador ──────────────────────────────────────────
echo ""
echo "PASO 5 — Puntuador (abriendo actuales y calculando métricas)"
echo "-------------------------------------------------------------"

python puntuador.py \
  --predictions resultados_sonnet/*.json \
  --actuals actuals_sellados.json \
  --out metricas_sonnet.json

python puntuador.py \
  --predictions resultados_opus/*.json \
  --actuals actuals_sellados.json \
  --out metricas_opus.json

echo ""
echo "============================================================"
echo "  ✓ Pipeline completo"
echo "  Resultados finales:"
echo "    metricas_sonnet.json"
echo "    metricas_opus.json"
echo "============================================================"
