#!/usr/bin/env python3
"""Paso 3: Genera el panel sintético de 850 personas y produce el ICC sintético (async)."""

import argparse
import asyncio
import json
import os
import random
import re
import statistics
from datetime import datetime
from pathlib import Path
import anthropic

CITY_DIST = {
    "Bogotá":       300,
    "Medellín":     160,
    "Cali":         150,
    "Barranquilla": 120,
    "Bucaramanga":  120,
}

STRATA_WEIGHTS     = {1: 0.20, 2: 0.35, 3: 0.25, 4: 0.10, 5: 0.07, 6: 0.03}
AGE_GROUPS         = ["18-25", "26-35", "36-45", "46-55", "56-65", "65+"]
AGE_WEIGHTS        = [0.15, 0.22, 0.20, 0.18, 0.15, 0.10]
EMPLOYMENT         = ["empleado_formal", "empleado_informal", "independiente",
                      "desempleado", "pensionado", "estudiante"]
EMPLOYMENT_WEIGHTS = [0.35, 0.20, 0.25, 0.10, 0.07, 0.03]
POLITICAL_WEIGHTS  = {"gobierno_petro": 0.30, "oposicion": 0.35, "independiente": 0.35}

NAMES_M = ["Carlos", "Juan", "Andrés", "Luis", "Jorge", "Miguel", "David",
           "Daniel", "Fernando", "Ricardo", "Camilo", "Sebastián"]
NAMES_F = ["María", "Claudia", "Alejandra", "Diana", "Patricia", "Laura",
           "Sandra", "Carolina", "Mónica", "Isabel", "Valentina", "Natalia"]

SURVEY_PROMPT = """\
Eres {nombre}, residente de {ciudad} (estrato {estrato}), {edad} años, {empleo}.

Contexto económico de {month_name}:
{context}

Responde las 5 preguntas de la Encuesta de Opinión del Consumidor de Fedesarrollo \
desde tu perspectiva personal y situación de hogar. Sé honesto/a con tu visión real.

P1 (ICE): La situación económica de tu hogar HOY, comparada con la de hace un año, es...
P2 (ICE): El momento actual para comprar bienes durables (electrodomésticos, muebles, vehículos) es...
P3 (IEC): La situación económica de tu hogar DENTRO DE UN AÑO, comparada con la actual, será...
P4 (IEC): Los próximos 12 meses para Colombia en general serán...
P5 (IEC): Las condiciones económicas del país dentro de 12 meses serán...

Responde ÚNICAMENTE con un JSON válido:
{{
  "p1": "MEJOR|IGUAL|PEOR",
  "p2": "BUEN_MOMENTO|INDIFERENTE|MAL_MOMENTO",
  "p3": "MEJOR|IGUAL|PEOR",
  "p4": "BUENOS_TIEMPOS|INDIFERENTE|MALOS_TIEMPOS",
  "p5": "MEJOR|IGUAL|PEOR",
  "nota": "una frase sobre tu situación específica"
}}"""

VALID = {
    "p1": {"MEJOR": 1, "IGUAL": 0, "PEOR": -1},
    "p2": {"BUEN_MOMENTO": 1, "INDIFERENTE": 0, "MAL_MOMENTO": -1},
    "p3": {"MEJOR": 1, "IGUAL": 0, "PEOR": -1},
    "p4": {"BUENOS_TIEMPOS": 1, "INDIFERENTE": 0, "MALOS_TIEMPOS": -1},
    "p5": {"MEJOR": 1, "IGUAL": 0, "PEOR": -1},
}

CONCURRENCY = 5   # max parallel API calls (conservador para evitar rate limits)


def make_persona(city, idx):
    gender = random.choice(["hombre", "mujer"])
    return {
        "id":      f"{city[:3].upper()}_{idx:04d}",
        "nombre":  random.choice(NAMES_M if gender == "hombre" else NAMES_F),
        "ciudad":  city,
        "estrato": random.choices(list(STRATA_WEIGHTS), weights=list(STRATA_WEIGHTS.values()))[0],
        "edad":    random.choices(AGE_GROUPS, weights=AGE_WEIGHTS)[0],
        "empleo":  random.choices(EMPLOYMENT, weights=EMPLOYMENT_WEIGHTS)[0],
        "politica":random.choices(list(POLITICAL_WEIGHTS), weights=list(POLITICAL_WEIGHTS.values()))[0],
        "genero":  gender,
    }


def parse_survey(text):
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if not match:
        return None, None
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return None, None
    scores = {}
    for q, mapping in VALID.items():
        raw = str(data.get(q, "")).upper().strip()
        scores[q] = mapping.get(raw)
    return scores, data.get("nota", "")


def calc_icc(responses):
    valid = [r for r in responses if all(r.get(f"p{i}") is not None for i in range(1, 6))]
    n = len(valid)
    if n == 0:
        return None

    def balance(q):
        vals = [r[q] for r in valid]
        pos = sum(1 for v in vals if v == 1) / n * 100
        neg = sum(1 for v in vals if v == -1) / n * 100
        return round(pos - neg, 2)

    b   = {f"p{i}": balance(f"p{i}") for i in range(1, 6)}
    ice = round((b["p1"] + b["p2"]) / 2, 2)
    iec = round((b["p3"] + b["p4"] + b["p5"]) / 3, 2)
    icc = round((b["p1"] + b["p2"] + b["p3"] + b["p4"] + b["p5"]) / 5, 2)
    return {"icc": icc, "ice": ice, "iec": iec, "balances": b, "n_valid": n, "n_total": len(responses)}


async def survey_persona(client, semaphore, model, persona, month_name, context_text):
    prompt = SURVEY_PROMPT.format(
        nombre=persona["nombre"], ciudad=persona["ciudad"], estrato=persona["estrato"],
        edad=persona["edad"], empleo=persona["empleo"],
        month_name=month_name, context=context_text,
    )
    async with semaphore:
        for attempt in range(4):
            try:
                rsp = await client.messages.create(
                    model=model, max_tokens=350,
                    messages=[{"role": "user", "content": prompt}]
                )
                scores, nota = parse_survey(rsp.content[0].text)
                if scores:
                    scores.update({
                        "persona_id": persona["id"],
                        "ciudad":     persona["ciudad"],
                        "estrato":    persona["estrato"],
                    })
                return scores
            except anthropic.RateLimitError:
                wait = 2 ** attempt * 5  # 5s, 10s, 20s, 40s
                print(f"  ⚠ rate limit {persona['id']} — reintentando en {wait}s")
                await asyncio.sleep(wait)
            except Exception as e:
                print(f"  ✗ error {persona['id']}: {type(e).__name__}: {e}")
                break
    return None


async def run_one(client, model, month_key, month_name, context_text, personas, run_idx, n_runs):
    print(f"\n{'='*60}")
    print(f"Run {run_idx+1}/{n_runs}  |  {model}  |  {month_name}")
    print(f"{'='*60}")

    semaphore  = asyncio.Semaphore(CONCURRENCY)
    counter    = {"done": 0}
    total      = len(personas)

    tasks = [
        survey_persona(client, semaphore, model, p, month_name, context_text)
        for p in personas
    ]

    responses  = []
    by_city    = {c: [] for c in CITY_DIST}
    by_strata  = {str(s): [] for s in STRATA_WEIGHTS}
    done       = 0

    for coro in asyncio.as_completed(tasks):
        result = await coro
        done  += 1
        if result:
            responses.append(result)
            by_city.setdefault(result["ciudad"], []).append(result)
            by_strata.setdefault(str(result["estrato"]), []).append(result)

        if done % 50 == 0 or done == total:
            m = calc_icc(responses)
            if m:
                spread = round(m["iec"] - m["ice"], 1)
                print(f"  [{done:4d}/{total}]  ICC={m['icc']:>+6.1f}  ICE={m['ice']:>+6.1f}  IEC={m['iec']:>+6.1f}  Spread={spread:>+6.1f}pp  n={m['n_valid']}")

    metrics        = calc_icc(responses)
    city_metrics   = {c: calc_icc(r) for c, r in by_city.items() if r}
    strata_metrics = {s: calc_icc(r) for s, r in by_strata.items() if r}

    if metrics:
        spread = round(metrics["iec"] - metrics["ice"], 1)
        print(f"\n  FINAL  ICC={metrics['icc']:>+6.1f}  ICE={metrics['ice']:>+6.1f}  IEC={metrics['iec']:>+6.1f}  Spread={spread:>+6.1f}pp  n={metrics['n_valid']}")
        print(f"\n  Por ciudad:")
        for city, cm in city_metrics.items():
            if cm:
                cs = round(cm["iec"] - cm["ice"], 1)
                print(f"    {city:<15} ICC={cm['icc']:>+6.1f}  ICE={cm['ice']:>+6.1f}  IEC={cm['iec']:>+6.1f}  Spread={cs:>+5.1f}  n={cm['n_valid']}")
        print(f"\n  Por estrato:")
        for s, sm in sorted(strata_metrics.items()):
            if sm:
                ss = round(sm["iec"] - sm["ice"], 1)
                print(f"    E-{s:<8} ICC={sm['icc']:>+6.1f}  ICE={sm['ice']:>+6.1f}  IEC={sm['iec']:>+6.1f}  Spread={ss:>+5.1f}  n={sm['n_valid']}")

    return {
        "run":        run_idx + 1,
        "model":      model,
        "month_key":  month_key,
        "month_name": month_name,
        "n_personas": len(personas),
        "metrics":    metrics,
        "by_city":    city_metrics,
        "by_strata":  strata_metrics,
        "timestamp":  datetime.utcnow().isoformat() + "Z",
    }


async def async_main(args):
    client = anthropic.AsyncAnthropic()

    with open(args.context) as f:
        ctx = json.load(f)

    month_key    = ctx["month_key"]
    month_name   = ctx["month_name"]
    context_text = ctx["context_text"]

    os.makedirs(args.out, exist_ok=True)

    scale    = min(args.max_personas, 850) / 850
    personas = []
    for city, count in CITY_DIST.items():
        for i in range(max(1, round(count * scale))):
            personas.append(make_persona(city, i))

    all_runs = []
    for run_idx in range(args.runs):
        run_data = await run_one(client, args.model, month_key, month_name,
                                 context_text, personas, run_idx, args.runs)
        all_runs.append(run_data)

    if len(all_runs) > 1:
        iccs = [r["metrics"]["icc"] for r in all_runs if r["metrics"]]
        aggregate = {
            "mean_icc": round(statistics.mean(iccs), 2),
            "std_icc":  round(statistics.stdev(iccs), 2) if len(iccs) > 1 else 0.0,
            "runs":     len(iccs),
        }
    else:
        aggregate = all_runs[0]["metrics"] if all_runs else None

    output = {
        "model":      args.model,
        "month_key":  month_key,
        "month_name": month_name,
        "runs":       all_runs,
        "aggregate":  aggregate,
        "timestamp":  datetime.utcnow().isoformat() + "Z",
    }

    slug    = args.model.replace("-", "_")
    outfile = Path(args.out) / f"resultado_{month_key}_{slug}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nGuardado → {outfile}")


def main():
    parser = argparse.ArgumentParser(description="Arnés de anclaje — panel sintético EOC (async)")
    parser.add_argument("--model",        required=True)
    parser.add_argument("--context",      required=True)
    parser.add_argument("--out",          required=True)
    parser.add_argument("--runs",         type=int, default=1)
    parser.add_argument("--max-personas", type=int, default=850, dest="max_personas")
    args = parser.parse_args()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
