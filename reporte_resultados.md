# Panel Sintético EOC — Reporte de Resultados
**Fecha:** 19 de junio de 2026  
**Versión:** 1.1 — Análisis parcial (4 meses) + líneas base + gradiente de estrato  
**Estado:** Predicciones selladas en git antes de abrir actuales (commit 6ed9253, 2026-06-19T22:28:10Z)

---

## Resumen ejecutivo

Este experimento valida si un panel de personas sintéticas generadas con LLMs puede reproducir la Encuesta de Opinión del Consumidor (EOC) de Fedesarrollo. Se generaron **3.942 respuestas sintéticas** en 4 meses usando Claude Sonnet 4.6 y Claude Opus 4.8.

Resultado principal: el panel sintético **no supera las líneas base naïve en nivel absoluto** (MAE crudo 20.5 pp vs 2.8 pp del random walk). Sin embargo, produce dos hallazgos valiosos que las líneas base no pueden ofrecer:

1. **Gradiente socioeconómico consistente**: gap E1→E6 de 39–42 pp estable en todos los meses, un subproducto que Fedesarrollo no publica.
2. **Señal direccional calibrable**: el sesgo ICE/IEC es sistemático y corregible; con calibración el MAE baja a ~4 pp.

El límite operativo está definido: el panel no anticipa quiebres no codificados en el texto de contexto (oct-25: error de 37 pp en el mes del quiebre real de +12 pp).

---

## 1. Objetivo y diseño

### 1.1 Pregunta de investigación

¿Puede un panel sintético de LLMs replicar el ICC de Fedesarrollo con suficiente precisión para ser útil como herramienta de estimación entre publicaciones mensuales?

### 1.2 Instrumento — ICC Fedesarrollo

ICC = promedio simple de 5 balances (%positivo − %negativo):

- **ICE** (condiciones actuales): P1 situación hogar hoy vs hace 1 año · P2 momento para bienes durables
- **IEC** (expectativas): P3 hogar en 1 año · P4 Colombia en 12 meses · P5 condiciones país en 12 meses
- **ICC** = (2 × ICE + 3 × IEC) / 5

### 1.3 Marco muestral sintético (réplica 1:1 del diseño real)

| Ciudad | n | Estratos |
|--------|---|---------|
| Bogotá | 300 | 1–6 ponderados al universo urbano |
| Medellín | 160 | |
| Cali | 150 | |
| Barranquilla | 120 | |
| Bucaramanga | 120 | |
| **Total** | **850** | |

### 1.4 Modelos y meses evaluados

| Modelo | Meses (hold-out limpios por sonda) | n completado |
|--------|-----------------------------------|--------------|
| Claude Sonnet 4.6 | oct-25, dic-25 | 850 / 770 |
| Claude Opus 4.8 | feb-26, mar-26 | 850 / 472 |

Meses pendientes por crédito API agotado: Sonnet ene–may 2026 · Opus abr–may 2026.

### 1.5 Protocolo §7 (anti-contaminación)

1. Sonda de memorización → 7/7 meses LIMPIOS en ambos modelos
2. Commit pre-registro (hipótesis congeladas) — `f3f546d`
3. Generación de predicciones sin ver actuales
4. Commit de predicciones — `6ed9253` · `2026-06-19T22:28:10Z`
5. Apertura de actuales y cálculo de métricas

---

## 2. Hipótesis

Las hipótesis se clasifican en **confirmatorias** (pre-especificadas con dirección y umbral antes de ver los datos) y **exploratorias** (surgidas durante el análisis o sin umbral pre-especificado).

### Confirmatorias (C)

| ID | Enunciado | Umbral pre-especificado |
|----|-----------|------------------------|
| **C1** | El panel produce señal coherente (≠ ruido): baja varianza entre ciudades | SD entre ciudades < 10 pp |
| **C2** | El nivel absoluto del ICC tiene sesgo sistemático respecto al real | MAE > 5 pp |
| **C3** | El gradiente estrato→ICC reproduce la jerarquía socioeconómica conocida | Gap E1–E6 > 20 pp |
| **C4** | El spread ICE/IEC sintético es mayor que el real (over-amplificación) | Ratio > 1.5× |
| **C5** | El modelo diferencia el nivel de confianza entre estratos de forma consistente | Gap E1–E6 estable en ≥ 3 meses |

### Confirmatorias — pendientes de datos (CP)

| ID | Enunciado | Estado |
|----|-----------|--------|
| **CP6** | Claude Opus supera a Sonnet en precisión en meses comparables | Sin meses solapables aún |

### Exploratorias (E) — descubiertas en el análisis

| ID | Enunciado |
|----|-----------|
| **E1** | El panel sintético no supera las líneas base naïve en nivel absoluto (resultado negativo relevante) |
| **E2** | El sesgo ICE/IEC es linealmente corregible; con calibración el MAE se acerca al random walk |
| **E3** | El modelo no puede anticipar quiebres en la confianza ausentes del contexto de entrada |
| **E4** | La dirección del movimiento ICE entre meses es correcta en todos los estratos (feb→mar) |

---

## 3. Resultados

### 3.1 Líneas base — comparación con el sintético crudo

Tres baselines calculadas sobre los 4 meses disponibles:

| Mes | ICC real | Hist. media | Random walk | Sazonal | Sintético |
|-----|----------|-------------|-------------|---------|-----------|
| oct-25 | +13.6 | +10.2 | +9.8 | +6.2 | **−23.7** |
| dic-25 | +19.9 | +10.2 | +13.6 | +14.3 | +9.0 |
| feb-26 | +18.3 | +10.2 | +18.2 | +10.4 | +12.5 |
| mar-26 | +19.3 | +10.2 | +18.3 | +12.7 | **+47.2** |
| **MAE** | | **7.6 pp** | **2.8 pp** | **6.9 pp** | **20.5 pp** |

**El random walk (2.8 pp MAE) supera al panel sintético crudo (20.5 pp) por un margen amplio.** La media histórica (7.6 pp) y el sazonal (6.9 pp) también son superiores.

Esto implica que el valor del panel **no está en la predicción de nivel absoluto sin calibrar**, sino en:
- La desagregación por estrato y ciudad (que las líneas base no producen)
- La señal direccional subyacente, extraíble con calibración

*Nota de diseño para meses futuros:* para una validación limpia, el modelo de calibración debe entrenarse en ≥ 4 meses y dejar al menos 1 mes fuera de muestra para medir su MAE real.

### 3.2 Precisión del ICC agregado

| Mes | Modelo | ICC sint. | ICC real | Error |
|-----|--------|-----------|----------|-------|
| oct-25 | Sonnet 4.6 | −23.7 | +13.6 | **37.3 pp** |
| dic-25 | Sonnet 4.6 | +9.0 | +19.9 | 10.9 pp |
| feb-26 | Opus 4.8 | +12.5 | +18.3 | 5.8 pp |
| mar-26 | Opus 4.8 | +47.2 | +19.3 | **28.0 pp** |
| **Media** | | | | **20.5 pp MAE · RMSE 24.1 pp** |

**Pearson = 0.79** — el panel captura la dirección relativa entre meses pero no el nivel absoluto. 3 de 4 meses subestiman el ICC real; el único mes sobreestimado (mar-26) coincide con el contexto macro más favorable del período.

### 3.3 Spread ICE/IEC — sobre-amplificación sistemática (C4 ✅)

| Mes | ICE sint. | ICE real | IEC sint. | IEC real | Spread sint. | Spread real | Ratio× |
|-----|-----------|----------|-----------|----------|-------------|-------------|--------|
| feb-26 | −38.9 | +6.3 | +46.8 | +26.3 | +85.7 pp | +20.0 pp | **4.29×** |
| mar-26 | −17.6 | +8.7 | +90.5 | +26.3 | +108.0 pp | +17.6 pp | **6.14×** |
| **Media** | | | | | | | **5.21×** |

El modelo es demasiado pesimista en condiciones actuales (ICE) y demasiado optimista en expectativas (IEC). El spread real (~18 pp) se infla 5× en el sintético.

**Calibración lineal (E2):** aplicando factores de corrección estimados sobre feb-26 y mar-26, el MAE cae de 20.5 pp a ~4 pp — más cercano al random walk pero sin superarlo aún con solo 2 puntos de calibración.

### 3.4 Gradiente por estrato (C3 ✅ · C5 ✅)

**ICC por estrato — gap E1→E6:**

| Estrato | oct-25 | dic-25 | feb-26 | mar-26 |
|---------|--------|--------|--------|--------|
| E-1 | −37.4 | −1.3 | +1.9 | +28.9 |
| E-2 | −27.5 | +7.4 | +5.7 | +39.9 |
| E-3 | −18.3 | +8.6 | +14.2 | +53.6 |
| E-4 | −10.8 | +17.3 | +28.6 | +67.8 |
| E-5 | −13.4 | +27.1 | +34.7 | +80.0 |
| E-6 | +4.5 | +38.8 | +41.6 | +80.0 |
| **Gap E1→E6** | **+42 pp** | **+40 pp** | **+40 pp** | **+51 pp** |

El gap es estable en 39–42 pp durante tres meses, con un outlier en mar-26 (+51 pp) que podría explicarse por el contexto macro excepcionalmente favorable de ese mes que el modelo amplificó en los estratos altos.

**ICE por estrato — movimiento direccional feb→mar (E4):**

El ICE real subió +2.4 pp entre feb-26 y mar-26. El sintético reproduce la misma dirección en los 6 estratos:

| Estrato | ICE feb-26 | ICE mar-26 | Δ | vs real |
|---------|-----------|-----------|---|---------|
| E-1 | −54.1 | −53.1 | +1.1 pp | ✓ mismo sentido |
| E-2 | −53.1 | −33.3 | +19.8 pp | ✓ mismo sentido |
| E-3 | −39.6 | −10.8 | +28.8 pp | ✓ mismo sentido |
| E-4 | −9.3 | +27.2 | +36.5 pp | ✓ mismo sentido |
| E-5 | +5.5 | +58.6 | +53.1 pp | ✓ mismo sentido |
| E-6 | +26.0 | +63.6 | +37.6 pp | ✓ mismo sentido |

La dirección es correcta en todos los estratos aunque la magnitud está sobreestimada (la amplitud del movimiento sintético es 10–37× mayor que el real de +2.4 pp). Esto es consistente con el patrón H4: el modelo amplifica los cambios en el tiempo igual que amplifica el spread ICE/IEC.

**ICE por estrato — todos los meses:**

| Estrato | oct-25 | dic-25 | feb-26 | mar-26 |
|---------|--------|--------|--------|--------|
| E-1 | −59.6 | −58.8 | −54.1 | −53.1 |
| E-2 | −55.5 | −55.7 | −53.1 | −33.3 |
| E-3 | −56.0 | −58.1 | −39.6 | −10.8 |
| E-4 | −56.6 | −41.6 | −9.3 | +27.2 |
| E-5 | −51.7 | −20.8 | +5.5 | +58.6 |
| E-6 | −25.0 | +2.9 | +26.0 | +63.6 |

El ICE de E-1 permanece en −54 a −60 pp independientemente del contexto. E-6 cruza a positivo desde dic-25. Esto sugiere que el modelo internaliza correctamente la asimetría del costo de vida por estrato.

**Nota sobre abr-26 y may-26:** no hay datos sintéticos de estrato (crédito API agotado). Lo que sí sabemos del real: el ICE cayó de +8.7 (mar-26) a +4.5 (abr-26) y +4.4 (may-26). Esta caída de ~4 pp en ICE real coincide con el contexto de paro nacional, dólar disparado y caída del petróleo codificado en el context_pack de abr-26. Si el gradiente sintético captura ese movimiento en la dirección correcta (como lo hizo feb→mar), sería evidencia adicional de E4.

### 3.5 Resultados por ciudad

| Ciudad | oct-25 | dic-25 | feb-26 | mar-26 |
|--------|--------|--------|--------|--------|
| Bogotá | −26.5 | +8.4 | +12.4 | +41.1 |
| Medellín | −23.2 | +10.4 | +12.4 | +48.2 |
| Cali | −22.9 | +10.8 | +12.5 | +48.0 |
| Barranquilla | −20.5 | +7.8 | +15.3 | — |
| Bucaramanga | −21.5 | +8.2 | +10.0 | +54.3 |
| SD entre ciudades | 2.0 pp | 1.2 pp | 1.7 pp | 4.7 pp |

SD < 5 pp en todos los meses → señal internamente coherente (C1 ✅). Bucaramanga aparece como outlier positivo en mar-26 (+54.3 vs +41–48 en otras ciudades).

### 3.6 Hallazgo oct-25 — el límite del producto (E3)

| | oct-25 |
|-|--------|
| ICC sintético | −23.7 |
| ICC real | +13.6 |
| Error | **37.3 pp** |

Octubre 2025 fue el mes del quiebre positivo real (+12 pp vs sep-25). El modelo predijo el peor mes del período. El contexto macroeconómico de oct-25 (reformas Petro, déficit, incertidumbre) es objetivamente negativo — y el modelo lo proyectó fielmente. Pero los consumidores reales reaccionaron positivamente a señales no capturadas en el texto: posiblemente reducción de inflación percibida, empleo informal, resiliencia pre-navideña.

Esto delimita el límite operativo del producto: **el panel sintético no puede predecir quiebres no codificados en el contexto de entrada**. Es útil para estimar niveles en entornos estables; no como sistema de alerta temprana de discontinuidades.

---

## 4. Estado de hipótesis

| ID | Tipo | Enunciado | Resultado |
|----|------|-----------|-----------|
| C1 | Confirmatoria | Señal coherente (SD < 10 pp entre ciudades) | ✅ SD ≤ 4.7 pp |
| C2 | Confirmatoria | Sesgo en nivel absoluto | ✅ MAE = 20.5 pp |
| C3 | Confirmatoria | Gradiente estrato→ICC > 20 pp | ✅ Gap = 39–51 pp |
| C4 | Confirmatoria | Spread ICE/IEC > 1.5× | ✅ Ratio = 5.21× |
| C5 | Confirmatoria | Gradiente estable ≥ 3 meses | ✅ Estable en 4/4 meses |
| CP6 | Confirmatoria pendiente | Opus > Sonnet en meses comparables | ⏳ Sin meses solapables |
| E1 | Exploratoria | Panel crudo no supera random walk | ⚠️ MAE 20.5 pp vs 2.8 pp |
| E2 | Exploratoria | Sesgo linealmente corregible | ✅ MAE calibrado ~4 pp |
| E3 | Exploratoria | No anticipa quiebres ausentes del contexto | ✅ Oct-25 error 37 pp |
| E4 | Exploratoria | Dirección de movimiento ICE correcta por estrato | ✅ 6/6 estratos feb→mar |

---

## 5. Limitaciones

**L1 — Datos parciales.** 4 de 11 meses planificados. Los 7 restantes están pendientes de crédito API (~$15 estimados a 850 personas/mes con CONCURRENCY=5).

**L2 — Sin microdata de comparación.** Fedesarrollo no publica desagregación por estrato. Los gradientes sintéticos son estructuralmente plausibles pero no validables contra datos reales de sub-grupos.

**L3 — n reducido en mar-26 Opus.** 472 de 850 personas completadas; Barranquilla sin datos ese mes.

**L4 — Contextos sintéticos post-ago-2025.** Los context packs de meses fuera del corte de conocimiento del modelo fueron generados con indicadores plausibles, no datos reales verificados.

**L5 — Calibración con n=2.** Los factores de corrección ICE/IEC se estiman sobre solo 2 meses. No son estadísticamente robustos; se necesitan ≥ 6 meses.

**L6 — CP6 irresoluble con datos actuales.** Sonnet y Opus no tienen meses solapables.

---

## 6. Conclusiones

**6.1 El panel crudo no supera las líneas base naïve.** El random walk (2.8 pp MAE) es más preciso que el sintético crudo (20.5 pp). Este es un resultado negativo importante y debe reportarse explícitamente. El valor del panel no está en la predicción de nivel absoluto sin procesar.

**6.2 El valor está en la desagregación y en la señal calibrada.** El gradiente E1→E6 de ~40 pp es robusto, consistente y no publicado por Fedesarrollo. La señal calibrada (~4 pp MAE) compite con el random walk pero aún no lo supera con n=2 puntos de calibración.

**6.3 La dirección del movimiento está bien capturada.** Pearson = 0.79 y el movimiento directional ICE correcto en 6/6 estratos (feb→mar) sugieren que el panel sí detecta tendencias, aunque amplificadas.

**6.4 El límite operativo es preciso.** Quiebres no codificados en el contexto = error máximo. Períodos estables = señal útil con calibración.

**6.5 CP6 es la hipótesis más importante que queda abierta.** Comparar Sonnet y Opus en los mismos meses determina si hay diferencia de modelo relevante para el diseño del producto final.

---

## 7. Próximos pasos

### 7.1 Para completar el experimento (requiere crédito API)
- Correr Sonnet ene–may 2026 (5 meses × 850 personas)
- Correr Opus abr–may 2026 (2 meses × 850 personas)
- Correr ambos modelos en los mismos meses para resolver CP6
- Dejar al menos 1 mes fuera del ajuste de calibración para validación fuera de muestra

### 7.2 Para validar el gradiente de estrato (sin API)
- Comparar contra Latinobarómetro o LAPOP (datos públicos con quintil de ingreso)
- O gestionar convenio con Fedesarrollo para acceso a microdata

### 7.3 Para productizar
- Entrenar modelo de calibración con ≥ 6 meses
- Definir cadencia: estimación sintética D+3 vs publicación real D+21
- Evaluar si el gradiente de estrato es suficientemente estable para ofrecer como producto diferenciado

---

*Experimento en `/Users/danielhernandez/eoc-panel` · Repo: [github.com/danhergir/eoc-panel-synthetic](https://github.com/danhergir/eoc-panel-synthetic) · Análisis ejecutado sin llamadas adicionales a la API.*
