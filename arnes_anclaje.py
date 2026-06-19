#!/usr/bin/env python3
"""Paso 3: Genera el panel sintético de 850 personas y produce el ICC sintético."""

import argparse
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

STRATA_WEIGHTS    = {1: 0.20, 2: 0.35, 3: 0.25, 4: 0.10, 5: 0.07, 6: 0.03}
AGE_GROUPS        = ["18-25", "26-35", "36-45", "46-55", "56-65", "65+"]
AGE_WEIGHTS       = [0.15, 0.22, 0.20, 0.18, 0.15, 0.10]
EMPLOYMENT        = ["empleado_formal", "empleado_informal", "independiente",
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


def make_persona(city, idx):
    gender = random.choice(["hombre", "mujer"])
    return {
        "id": f"{city[:3].upper()}_{idx:04d}",
        "nombre": random.choice(NAMES_M if gender == "hombre" else NAMES_F),
        "ciudad": city,
        "estrato": random.choices(list(STRATA_WEIGHTS), weights=list(STRATA_WEIGHTS.values()))[0],
        "edad": random.choices(AGE_GROUPS, weights=AGE_WEIGHTS)[0],
        "empleo": random.choices(EMPLOYMENT, weights=EMPLOYMENT_WEIGHTS)[0],
        "politica": random.choices(list(POLITICAL_WEIGHTS), weights=list(POLITICAL_WEIGHTS.values()))[0],
        "genero": gender,
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

    b = {f"p{i}": balance(f"p{i}") for i in range(1, 6)}
    ice = round((b["p1"] + b["p2"]) / 2, 2)
    iec = round((b["p3"] + b["p4"] + b["p5"]) / 3, 2)
    icc = round((b["p1"] + b["p2"] + b["p3"] + b["p4"] + b["p5"]) / 5, 2)
    return {"icc": icc, "ice": ice, "iec": iec, "balances": b, "n_valid": n, "n_total": len(responses)}


def main():
    parser = argparse.ArgumentParser(description="Arnés de anclaje — panel sintético EOC")
    parser.add_argument("--model",       required=True)
    parser.add_argument("--context",     required=True, help="context_pack_YYYY_MM.json")
    parser.add_argument("--out",         required=True, help="Carpeta de salida")
    parser.add_argument("--runs",        type=int, default=1)
    parser.add_argument("--max-personas", type=int, default=850, dest="max_personas")
    args = parser.parse_args()

    client = anthropic.Anthropic()

    with open(args.context) as f:
        ctx = json.load(f)

    month_key    = ctx["month_key"]
    month_name   = ctx["month_name"]
    context_text = ctx["context_text"]

    os.makedirs(args.out, exist_ok=True)
    all_runs = []

    for run_idx in range(args.runs):
        print(f"\n{'='*55}")
        print(f"Run {run_idx+1}/{args.runs}  |  {args.model}  |  {month_name}")
        print(f"{'='*55}")

        scale = min(args.max_personas, 850) / 850
        personas = []
        for city, count in CITY_DIST.items():
            for i in range(max(1, round(count * scale))):
                personas.append(make_persona(city, i))

        responses = []
        by_city   = {c: [] for c in CITY_DIST}

        for i, p in enumerate(personas):
            prompt = SURVEY_PROMPT.format(
                nombre=p["nombre"], ciudad=p["ciudad"], estrato=p["estrato"],
                edad=p["edad"], empleo=p["empleo"],
                month_name=month_name, context=context_text,
            )
            try:
                rsp = client.messages.create(
                    model=args.model, max_tokens=350,
                    messages=[{"role": "user", "content": prompt}]
                )
                scores, nota = parse_survey(rsp.content[0].text)
                if scores:
                    scores.update({"persona_id": p["id"], "ciudad": p["ciudad"], "estrato": p["estrato"]})
                    responses.append(scores)
                    by_city[p["ciudad"]].append(scores)
                else:
                    print(f"  [{i+1:4d}] parse error — {p['id']}")
            except Exception as e:
                print(f"  [{i+1:4d}] API error: {e}")

            if (i + 1) % 10 == 0:
                m = calc_icc(responses)
                if m:
                    print(f"  [{i+1:4d}/{len(personas)}]  ICC={m['icc']:+.1f}  ICE={m['ice']:+.1f}  IEC={m['iec']:+.1f}  n={m['n_valid']}")

        metrics      = calc_icc(responses)
        city_metrics = {c: calc_icc(r) for c, r in by_city.items() if r}

        if metrics:
            print(f"\n  FINAL  ICC={metrics['icc']:+.1f}  ICE={metrics['ice']:+.1f}  IEC={metrics['iec']:+.1f}  n={metrics['n_valid']}")

        all_runs.append({
            "run": run_idx + 1,
            "model": args.model,
            "month_key": month_key,
            "month_name": month_name,
            "n_personas": len(personas),
            "metrics": metrics,
            "by_city": city_metrics,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })

    if len(all_runs) > 1:
        iccs = [r["metrics"]["icc"] for r in all_runs if r["metrics"]]
        aggregate = {
            "mean_icc": round(statistics.mean(iccs), 2),
            "std_icc":  round(statistics.stdev(iccs), 2) if len(iccs) > 1 else 0.0,
            "runs": len(iccs),
        }
    else:
        aggregate = all_runs[0]["metrics"] if all_runs else None

    output = {
        "model": args.model,
        "month_key": month_key,
        "month_name": month_name,
        "runs": all_runs,
        "aggregate": aggregate,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    slug    = args.model.replace("-", "_")
    outfile = Path(args.out) / f"resultado_{month_key}_{slug}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nGuardado → {outfile}")


if __name__ == "__main__":
    main()
