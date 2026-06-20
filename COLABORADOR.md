# Instrucciones para el colaborador — Panel Sintético EOC

Gracias por correr estos experimentos. Acá va todo lo que necesitás saber.

---

## Qué es esto

Un experimento que evalúa si personas sintéticas generadas con LLMs pueden reproducir la Encuesta de Opinión del Consumidor (EOC) de Fedesarrollo en Colombia. El script genera 850 personas virtuales, les aplica la encuesta, y calcula el ICC (Índice de Confianza del Consumidor) sintético.

---

## Setup (5 minutos)

### 1. Clonar el repo

```bash
git clone https://github.com/danhergir/eoc-panel-synthetic.git
cd eoc-panel-synthetic
```

### 2. Instalar dependencias

```bash
pip install anthropic
```

### 3. Configurar tu API key de Anthropic

Necesitás una API key de [console.anthropic.com](https://console.anthropic.com) con saldo disponible.

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Para que persista en tu sesión podés agregarlo a tu `.zshrc` o `.bashrc`.

---

## Qué ya está corrido

| Mes | Modelo | Estado | n válido |
|-----|--------|--------|----------|
| oct-25 | Sonnet 4.6 | ✅ completo | 850 |
| dic-25 | Sonnet 4.6 | ✅ completo | 770 |
| feb-26 | Opus 4.8 | ✅ completo | 850 |
| mar-26 | Opus 4.8 | ⚠️ parcial | 472/850 |

---

## Qué necesitamos que corras

### Pendiente Sonnet (5 meses)

```bash
MONTHS=("2026_01" "2026_02" "2026_03" "2026_04" "2026_05")

for MONTH in "${MONTHS[@]}"; do
  echo ">>> Sonnet / $MONTH"
  python3 arnes_anclaje.py \
    --model claude-sonnet-4-6 \
    --context "context_pack_${MONTH}.json" \
    --out resultados_sonnet \
    --runs 1 \
    --max-personas 850
done
```

O directamente:

```bash
bash run_sonnet_pendiente.sh
```

### Pendiente Opus (3 meses — incluye repetir mar-26 completo)

```bash
MONTHS=("2026_03" "2026_04" "2026_05")

for MONTH in "${MONTHS[@]}"; do
  echo ">>> Opus / $MONTH"
  python3 arnes_anclaje.py \
    --model claude-opus-4-8 \
    --context "context_pack_${MONTH}.json" \
    --out resultados_opus \
    --runs 1 \
    --max-personas 850
done
```

O directamente:

```bash
bash run_opus_pendiente.sh
```

---

## Tiempo y costo estimado

| Modelo | Meses | Personas/mes | Tiempo aprox. |
|--------|-------|--------------|---------------|
| Sonnet 4.6 | 5 | 850 | ~45 min/mes |
| Opus 4.8 | 3 | 850 | ~60 min/mes |

El script corre con `CONCURRENCY=5` (5 llamadas paralelas) para no exceder rate limits. Si ves errores de rate limit, el script reintenta automáticamente con backoff exponencial.

---

## Cómo compartir los resultados

Una vez que terminen, compartí los archivos JSON generados en `resultados_sonnet/` y `resultados_opus/`. Podés:

- Hacer un fork del repo, pushear los resultados, y abrir un PR
- O simplemente compartir los archivos directamente

Los archivos que esperamos recibir:

```
resultados_sonnet/resultado_2026_01_claude_sonnet_4_6.json
resultados_sonnet/resultado_2026_02_claude_sonnet_4_6.json
resultados_sonnet/resultado_2026_03_claude_sonnet_4_6.json
resultados_sonnet/resultado_2026_04_claude_sonnet_4_6.json
resultados_sonnet/resultado_2026_05_claude_sonnet_4_6.json
resultados_opus/resultado_2026_03_claude_opus_4_8.json   ← repetir completo
resultados_opus/resultado_2026_04_claude_opus_4_8.json
resultados_opus/resultado_2026_05_claude_opus_4_8.json
```

---

## Si algo falla

El error más común es crédito insuficiente:

```
BadRequestError: Your credit balance is too low
```

En ese caso el script guarda un JSON vacío (n=0). No pasa nada — simplemente recargá crédito y volvé a correr ese mes.

Para ver el progreso en tiempo real, el script imprime el ICC cada 50 personas:

```
[  50/850]  ICC= +12.4  ICE= -38.5  IEC= +46.7  n=50
[ 100/850]  ICC= +12.6  ICE= -38.7  IEC= +46.8  n=100
```

---

## Contexto del experimento (opcional)

El reporte completo con metodología y resultados parciales está en [`reporte_resultados.md`](reporte_resultados.md).
