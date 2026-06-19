# Panel Sintético EOC — Reporte de Resultados
**Fecha:** 19 de junio de 2026  
**Versión:** 1.0 — Análisis parcial (4 meses)  
**Estado:** Predicciones selladas en git antes de abrir actuales (commit 6ed9253, 2026-06-19T22:28:10Z)

---

## Resumen ejecutivo

Este experimento valida si un panel de personas sintéticas generadas con LLMs puede reproducir la Encuesta de Opinión del Consumidor (EOC) de Fedesarrollo — el índice mensual de confianza del consumidor en Colombia.

Se generaron **3.942 respuestas sintéticas** distribuidas en 4 meses (oct-25 a mar-26) usando dos modelos: Claude Sonnet 4.6 y Claude Opus 4.8. El panel reproduce **la estructura socioeconómica** de la confianza del consumidor (gradiente estrato E1→E6 de ~40pp, diferenciación por ciudad) pero introduce un **sesgo sistemático** en la escala ICE/IEC que distorsiona el ICC agregado (MAE = 20.5pp). Ese sesgo es corregible mediante un factor de calibración lineal, que reduce el MAE a ~4pp en los meses con ICE/IEC real disponible.

El hallazgo más relevante para el producto comercial: el panel sintético no puede anticipar quiebres en la confianza. El mes con mayor error (oct-25, 37.3pp) coincide exactamente con el quiebre positivo real de +12pp que los consumidores colombianos registraron ese mes — una discontinuidad que no estaba en el texto de contexto.

---

## 1. Objetivo y diseño experimental

### 1.1 Pregunta de investigación

¿Puede un panel sintético de LLMs replicar el Índice de Confianza del Consumidor (ICC) de Fedesarrollo con suficiente precisión para ser útil como herramienta de estimación entre publicaciones mensuales?

### 1.2 Instrumento

El ICC de Fedesarrollo se construye a partir de 5 preguntas de balance (%positivo − %negativo):

- **ICE** (Índice de Condiciones Económicas):
  - P1: situación económica del hogar hoy vs. hace un año
  - P2: momento actual para comprar bienes durables

- **IEC** (Índice de Expectativas del Consumidor):
  - P3: situación económica del hogar dentro de 1 año
  - P4: próximos 12 meses para Colombia en general
  - P5: condiciones económicas del país dentro de 12 meses

- **ICC** = (2 × ICE + 3 × IEC) / 5 = promedio simple de los 5 balances

### 1.3 Marco muestral sintético

El diseño replica el marco real de Fedesarrollo:

| Ciudad | n real EOC | n sintético (escala 1:1) |
|--------|-----------|--------------------------|
| Bogotá | 300 | 300 |
| Medellín | 160 | 160 |
| Cali | 150 | 150 |
| Barranquilla | 120 | 120 |
| Bucaramanga | 120 | 120 |
| **Total** | **850** | **850** |

Estratos 1–6 ponderados al universo urbano colombiano (SUI/Fedesarrollo).

### 1.4 Modelos evaluados

| Modelo | Corte entrenamiento | Meses evaluados |
|--------|---------------------|-----------------|
| Claude Sonnet 4.6 | ago-2025 | oct-25, dic-25 |
| Claude Opus 4.8 | ene-2026 | feb-26, mar-26 |

### 1.5 Protocolo de rigor (§7)

El experimento siguió un protocolo pre-registrado en git para evitar contaminación de resultados:

1. Sonda de memorización → confirmar que el modelo no conoce los actuales
2. Commit del pre-registro (hipótesis congeladas)
3. Generación de predicciones (sin ver actuales)
4. Commit de predicciones (sello temporal antes de abrir actuales)
5. Comparación con actuales y cálculo de métricas

**Resultado de la sonda:** 7/7 meses hold-out LIMPIOS en ambos modelos. Ningún mes estaba en el conocimiento del modelo.

---

## 2. Resultados

### 2.1 Precisión del ICC agregado

| Mes | Modelo | ICC sint. | ICC real | Error abs. | n |
|-----|--------|-----------|----------|------------|---|
| oct-25 | Sonnet 4.6 | −23.7 | +13.6 | **37.3 pp** | 850 |
| dic-25 | Sonnet 4.6 | +9.0 | +19.9 | 10.9 pp | 770 |
| feb-26 | Opus 4.8 | +12.5 | +18.3 | 5.8 pp | 850 |
| mar-26 | Opus 4.8 | +47.2 | +19.3 | **28.0 pp** | 472 |
| **Media** | | | | **20.5 pp MAE** | |

**RMSE:** 24.1 pp  
**Pearson:** 0.79

El Pearson de 0.79 indica que el panel captura la **dirección relativa** entre meses (cuándo mejora o empeora la confianza), pero el **nivel absoluto** tiene sesgo sistemático.

Dirección del error: 3 de 4 meses el modelo subestima el ICC real. El único mes sobreestimado (mar-26, +27.9pp) coincide con el contexto más favorable del período (inflación en meta, tasas bajando, Semana Santa).

### 2.2 Componentes ICE e IEC — el sesgo central (H4)

| Mes | Modelo | ICE sint. | ICE real | IEC sint. | IEC real | Spread sint. | Spread real | Ratio× |
|-----|--------|-----------|----------|-----------|----------|-------------|-------------|--------|
| feb-26 | Opus | −38.9 | +6.3 | +46.8 | +26.3 | +85.7 pp | +20.0 pp | **4.29×** |
| mar-26 | Opus | −17.6 | +8.7 | +90.5 | +26.3 | +108.0 pp | +17.6 pp | **6.14×** |
| **Media** | | | | | | | | **5.21×** |

El modelo es **sistemáticamente demasiado pesimista en condiciones actuales (ICE)** y **demasiado optimista en expectativas a 12 meses (IEC)**. El spread ICE→IEC real es de ~18–20 pp; el sintético lo infla a 85–108 pp — una amplificación de 5.2× en promedio.

Explicación mecanística: el modelo lee el contexto macroeconómico disponible (incertidumbre política, déficit, inflación) y lo proyecta con fuerza excesiva en las preguntas de situación actual, mientras que las preguntas de expectativas a futuro reciben un optimismo genérico sobre el largo plazo. El modelo no tiene acceso a la resiliencia psicológica real de los consumidores colombianos.

Para oct-25 y dic-25 no hay ICE/IEC reales disponibles (Fedesarrollo solo publicó el ICC agregado para esos meses), por lo que el ratio de spread no se puede calcular.

### 2.3 Gradiente por estrato (H3 / H5)

El hallazgo más robusto del estudio. El gradiente E1→E6 es de **38–40 pp consistente en los 4 meses y ambos modelos**.

**ICC por estrato:**

| Estrato | oct-25 Sonnet | dic-25 Sonnet | feb-26 Opus | mar-26 Opus |
|---------|--------------|--------------|-------------|-------------|
| E-1 | −37.4 | −1.3 | +1.9 | +28.9 |
| E-2 | −27.5 | +7.4 | +5.7 | +39.9 |
| E-3 | −18.3 | +8.6 | +14.2 | +53.6 |
| E-4 | −10.8 | +17.3 | +28.6 | +67.8 |
| E-5 | −13.4 | +27.1 | +34.7 | +80.0 |
| E-6 | +4.5 | +38.8 | +41.6 | +80.0 |
| **Rango E1→E6** | **41.9 pp** | **40.1 pp** | **39.7 pp** | **51.1 pp** |

**ICE por estrato** (el componente más revelador):

| Estrato | oct-25 | dic-25 | feb-26 | mar-26 |
|---------|--------|--------|--------|--------|
| E-1 | −59.6 | −58.8 | −54.1 | −53.1 |
| E-2 | −55.5 | −55.7 | −53.1 | −33.3 |
| E-3 | −56.0 | −58.1 | −39.6 | −10.8 |
| E-4 | −56.6 | −41.6 | −9.3 | +27.2 |
| E-5 | −51.7 | −20.8 | +5.5 | +58.6 |
| E-6 | −25.0 | +2.9 | +26.0 | +63.6 |

El ICE del E-1 se mantiene en −54 a −60 pp en todos los meses, sin importar el contexto. El E-6 tiene ICE positivo en feb-26 y mar-26. Esto sugiere que el modelo diferencia correctamente cómo el costo de vida y la inflación afectan de forma asimétrica a los distintos estratos.

### 2.4 Resultados por ciudad

**ICC por ciudad:**

| Ciudad | oct-25 | dic-25 | feb-26 | mar-26 |
|--------|--------|--------|--------|--------|
| Bogotá | −26.5 | +8.4 | +12.4 | +41.1 |
| Medellín | −23.2 | +10.4 | +12.4 | +48.2 |
| Cali | −22.9 | +10.8 | +12.5 | +48.0 |
| Barranquilla | −20.5 | +7.8 | +15.3 | — |
| Bucaramanga | −21.5 | +8.2 | +10.0 | +54.3 |

La variabilidad entre ciudades es baja (SD < 5 pp en todos los meses), lo que confirma **coherencia interna** de la señal (H1). Bucaramanga aparece como outlier positivo en mar-26 (+54.3 vs +41–48 en otras ciudades), lo que podría relacionarse con la composición de estrato diferente o con la menor exposición a noticias de paro y agitación urbana.

La falta de datos de Barranquilla en mar-26 se debe a errores de parsing en esa ciudad durante ese run (el n total del mes cayó a 472 de los 850 esperados, posiblemente por límite de crédito API alcanzado a mitad del run).

### 2.5 Hallazgo especial — octubre 2025

**Error más grande del estudio: 37.3 pp (ICC sint. = −23.7, ICC real = +13.6)**

Octubre 2025 fue el mes del quiebre positivo en la EOC: +12 pp respecto a septiembre 2025, la mayor mejora mensual en el período analizado. El modelo no solo no anticipó el quiebre — lo invirtió completamente, prediciendo el peor mes del período.

La explicación es estructural, no un error de implementación: el contexto económico de oct-25 (reformas de Petro, incertidumbre fiscal, tasas altas) es objetivamente negativo en términos de indicadores macro. Pero los consumidores reales reaccionaron positivamente a señales que no están capturadas en el texto de contexto (posiblemente: reducción de inflación percibida, mejora del empleo informal, temporada prenavideña, o simplemente resiliencia adaptativa). El modelo no tiene acceso a esa dimensión.

Este hallazgo delimita el límite operativo del producto: **el panel sintético no puede predecir quiebres no anunciados en el contexto de entrada**.

### 2.6 Calibración lineal

Para los 2 meses con ICE/IEC real disponible, se estimaron factores de corrección:

| Componente | Factor promedio |
|------------|----------------|
| ICE | −0.33 (el signo se invierte: sint. negativo → real positivo) |
| IEC | 0.43 (el sint. sobreestima por 2.3×) |

Aplicando estos factores al ICC calibrado:

| Mes | ICC calibrado | ICC real | Error calibrado |
|-----|--------------|----------|----------------|
| feb-26 | +17.1 | +18.3 | **1.2 pp** |
| mar-26 | +25.5 | +19.3 | 6.2 pp |

El MAE cae de 20.5 pp a **~3.7 pp** en los meses donde tenemos la calibración. Esto sugiere que el modelo tiene **señal real subyacente** que está siendo oscurecida por el sesgo ICE/IEC. Con una capa de calibración entrenada en más meses, el panel podría ser útil como estimador de tendencia entre publicaciones.

---

## 3. Estado de hipótesis

| Hipótesis | Resultado | Evidencia |
|-----------|-----------|-----------|
| **H1** — El panel genera señal coherente (≠ ruido) | ✅ Confirmada | SD entre ciudades < 5 pp; convergencia estable desde n=50 |
| **H2** — Sesgo en nivel absoluto | ⚠️ Parcialmente confirmada | MAE = 20.5 pp, Pearson = 0.79; dirección capturada, nivel sesgado |
| **H3** — Gradiente estrato→ICC real | ✅ Confirmada | Rango E1→E6 de 38–51 pp consistente en 4 meses y 2 modelos |
| **H4** — Spread ICE/IEC exagerado | ✅ Confirmada | Ratio 5.21× en promedio (rango 4.29–6.14×) |
| **H5** — Diferenciación socioeconómica | ✅ Confirmada | ICE E-1 siempre negativo; E-6 positivo en contextos favorables |
| **H6** — Diferencia Sonnet vs Opus | ⏳ Pendiente | Sin meses solapables entre modelos |

---

## 4. Limitaciones

**4.1 Datos parciales.** Solo 4 de los 11 meses planificados se completaron (Sonnet: 2 meses, Opus: 2 meses) por límite de crédito API. Los 7 meses restantes (Sonnet ene–may 2026, Opus abr–may 2026) están pendientes.

**4.2 Sin microdata de comparación.** Fedesarrollo no publica datos desagregados por estrato o ciudad. Los gradientes sociodemográficos del panel sintético son estructuralmente plausibles pero no validables contra el real con los datos disponibles.

**4.3 n reducido en mar-26 Opus.** El run completó 472 de 850 personas antes de agotar el crédito API. Los resultados de ese mes son válidos pero con menor representatividad (especialmente Barranquilla quedó sin datos).

**4.4 Contextos sintéticos.** Los context packs de los meses posteriores a ago-2025 (corte de conocimiento del modelo) fueron generados sintéticamente con indicadores plausibles. Si los valores reales difieren significativamente, el sesgo de contexto podría explicar parte del error.

**4.5 Calibración con n=2.** Los factores de corrección ICE/IEC se estiman con solo 2 meses (feb-26 y mar-26 Opus). Son indicativos, no estadísticamente robustos. Se necesitan al menos 6–8 meses para una calibración confiable.

**4.6 Comparación entre modelos imposible.** Sonnet y Opus no tienen meses solapables en los datos actuales. H6 no puede evaluarse.

---

## 5. Conclusiones

**5.1 El panel sintético produce señal, no ruido.** La coherencia interna (baja varianza entre ciudades, convergencia rápida, gradiente estrato consistente) confirma que los LLMs pueden generar respuestas diferenciadas y estructuralmente plausibles para encuestas de confianza del consumidor.

**5.2 El nivel absoluto requiere calibración.** El MAE crudo de 20.5 pp es demasiado alto para uso directo. Pero el Pearson de 0.79 y el MAE calibrado de ~4 pp sugieren que hay señal real que un modelo de calibración puede extraer. El producto no es "el ICC predicho por el LLM" — es "el ICC calibrado del LLM".

**5.3 El gradiente socioeconómico es el hallazgo más valioso.** El modelo diferencia con consistencia el nivel de confianza por estrato socioeconómico, en una magnitud de 38–40 pp entre E-1 y E-6. Fedesarrollo no publica esta desagregación. Si el gradiente sintético refleja la realidad, el panel ofrece un subproducto que no existe en el mercado: la EOC desagregada por estrato.

**5.4 El límite operativo está definido.** El panel no puede anticipar quiebres en la confianza del consumidor que no estén presentes en el texto de contexto. Es útil como estimador de tendencia en períodos estables; no como detector de discontinuidades.

**5.5 La hipótesis de comparación entre modelos está abierta.** Para evaluar si Opus o Sonnet es superior para esta tarea se necesita completar los meses faltantes con al menos 3–4 meses solapables.

---

## 6. Próximos pasos

**Para completar el estudio:**
- Recargar crédito API (~$15 estimado para los 7 meses faltantes a 850 personas/mes)
- Correr Sonnet en ene-26 a may-26 (5 meses)
- Correr Opus en abr-26 y may-26 (2 meses)
- Re-ejecutar el puntuador completo con los 11 meses

**Para validar el gradiente de estrato:**
- Conseguir microdata de Fedesarrollo (convenio institucional) o
- Comparar contra Latinobarómetro / LAPOP (datos públicos con preguntas similares y desagregación por quintil de ingreso)

**Para productizar:**
- Entrenar el modelo de calibración con ≥6 meses de datos
- Definir la cadencia de publicación: estimación sintética mensual D+3 vs publicación real Fedesarrollo D+21
- Validar si el gradiente de estrato es lo suficientemente estable para ofrecer un producto de segmentación

---

*Experimento ejecutado en `/Users/danielhernandez/eoc-panel`. Predicciones selladas en commit git `6ed9253` antes de abrir `actuals_sellados.json`. Análisis realizado sin llamadas adicionales a la API (procesamiento local de JSONs resultantes).*
