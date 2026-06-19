#!/usr/bin/env python3
"""Paso 1: Detecta qué meses del hold-out ya conoce el modelo (datos contaminados)."""

import argparse
import json
import re
import sys
from datetime import datetime
import anthropic

MONTH_NAMES = {
    "2025_10": "octubre de 2025",
    "2025_12": "diciembre de 2025",
    "2026_01": "enero de 2026",
    "2026_02": "febrero de 2026",
    "2026_03": "marzo de 2026",
    "2026_04": "abril de 2026",
    "2026_05": "mayo de 2026",
}

PROBE_PROMPT = """Eres un asistente experto en estadísticas económicas de Colombia.

Pregunta directa: ¿Cuál fue el valor del ICC (Índice de Confianza del Consumidor) \
de Fedesarrollo publicado para {month}?

El ICC de Fedesarrollo es un número que suele estar entre -100 y +100, \
aunque en los últimos años ha oscilado entre -10 y +30.

Si conoces el valor exacto o aproximado (con alta o media confianza), indícalo.
Si no lo sabes con certeza, di "no sé" o indica un rango amplio con baja confianza.

Responde SOLO con un JSON válido, sin texto adicional:
{{"icc_estimado": <número o null si no sabes>, "confianza": "<alta|media|baja>", "razonamiento": "<una línea breve>"}}"""


def probe_month(client, model, month_key, month_name):
    prompt = PROBE_PROMPT.format(month=month_name)
    response = client.messages.create(
        model=model,
        max_tokens=250,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text.strip()
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"icc_estimado": None, "confianza": "baja", "razonamiento": text[:120]}


def main():
    parser = argparse.ArgumentParser(description="Sonda de memorización del modelo sobre la EOC")
    parser.add_argument("--model", required=True, help="ID del modelo (ej: claude-sonnet-4-6)")
    parser.add_argument("--actuals", required=True, help="Ruta a actuals_sellados.json")
    parser.add_argument("--out", required=True, help="Archivo de salida JSON")
    args = parser.parse_args()

    client = anthropic.Anthropic()

    with open(args.actuals) as f:
        actuals = json.load(f)

    results = {}
    contaminated = []
    clean = []

    print(f"\nSondeando memorización: {args.model}")
    print("-" * 50)

    for month_key, month_name in MONTH_NAMES.items():
        actual_data = actuals.get(month_key, {})
        actual_icc = actual_data.get("icc")
        if actual_icc is None:
            print(f"  {month_name}: sin actual, omitiendo")
            continue

        probe = probe_month(client, args.model, month_key, month_name)
        est = probe.get("icc_estimado")
        confianza = probe.get("confianza", "baja")

        is_contaminated = False
        if est is not None and confianza in ("alta", "media"):
            try:
                delta = abs(float(est) - float(actual_icc))
                is_contaminated = delta <= 2.5
            except (TypeError, ValueError):
                pass

        status = "CONTAMINADO" if is_contaminated else "LIMPIO"
        results[month_key] = {
            "month": month_name,
            "actual_icc": actual_icc,
            "model_estimate": est,
            "confianza": confianza,
            "razonamiento": probe.get("razonamiento", ""),
            "status": status,
        }

        if is_contaminated:
            contaminated.append(month_key)
        else:
            clean.append(month_key)

        marker = "⚠️ " if is_contaminated else "✓  "
        print(f"  {marker}{month_name}: actual={actual_icc:+.1f}  estimado={est}  [{confianza}]  → {status}")

    output = {
        "model": args.model,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "contaminated_months": contaminated,
        "clean_months": clean,
        "n_contaminated": len(contaminated),
        "n_clean": len(clean),
        "details": results,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("-" * 50)
    print(f"Meses limpios    ({len(clean)}): {', '.join(MONTH_NAMES[k] for k in clean)}")
    print(f"Meses contaminados ({len(contaminated)}): {', '.join(MONTH_NAMES[k] for k in contaminated)}")
    print(f"\nResultado → {args.out}")


if __name__ == "__main__":
    main()
