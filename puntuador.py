#!/usr/bin/env python3
"""Paso 5: Compara predicciones sintéticas con actuales y calcula métricas de calibración."""

import argparse
import json
import math
from datetime import datetime


def mae(p, a):
    return abs(p - a)


def rmse(ps, as_):
    return math.sqrt(sum((p - a) ** 2 for p, a in zip(ps, as_)) / len(ps))


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num   = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denom = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return round(num / denom, 4) if denom else None


def spread_ratio(pred_ice, pred_iec, actual_ice, actual_iec):
    """ICE/IEC spread sintético vs real — cuántas veces más grande es el spread del modelo."""
    if None in (pred_ice, pred_iec, actual_ice, actual_iec):
        return None
    synth_spread = abs(pred_iec - pred_ice)
    real_spread  = abs(actual_iec - actual_ice)
    if real_spread == 0:
        return None
    return round(synth_spread / real_spread, 2)


def strata_analysis(runs):
    """Calcula ICC/ICE/IEC por estrato agregando respuestas individuales de todos los runs."""
    by_stratum = {}
    for run in runs:
        for resp in run.get("_responses", []):
            s = resp.get("estrato")
            if s is None:
                continue
            key = str(s)
            if key not in by_stratum:
                by_stratum[key] = []
            by_stratum[key].append(resp)

    result = {}
    for stratum, resps in sorted(by_stratum.items()):
        valid = [r for r in resps if all(r.get(f"p{i}") is not None for i in range(1, 6))]
        n = len(valid)
        if n == 0:
            continue

        def bal(q):
            vals = [r[q] for r in valid]
            pos = sum(1 for v in vals if v == 1) / n * 100
            neg = sum(1 for v in vals if v == -1) / n * 100
            return round(pos - neg, 2)

        b = {f"p{i}": bal(f"p{i}") for i in range(1, 6)}
        result[stratum] = {
            "n": n,
            "icc": round((b["p1"]+b["p2"]+b["p3"]+b["p4"]+b["p5"]) / 5, 2),
            "ice": round((b["p1"]+b["p2"]) / 2, 2),
            "iec": round((b["p3"]+b["p4"]+b["p5"]) / 3, 2),
            "balances": b,
        }
    return result


def city_analysis(runs):
    """Calcula ICC/ICE/IEC por ciudad agregando respuestas individuales de todos los runs."""
    by_city = {}
    for run in runs:
        for resp in run.get("_responses", []):
            city = resp.get("ciudad")
            if not city:
                continue
            if city not in by_city:
                by_city[city] = []
            by_city[city].append(resp)

    result = {}
    for city, resps in sorted(by_city.items()):
        valid = [r for r in resps if all(r.get(f"p{i}") is not None for i in range(1, 6))]
        n = len(valid)
        if n == 0:
            continue

        def bal(q):
            vals = [r[q] for r in valid]
            pos = sum(1 for v in vals if v == 1) / n * 100
            neg = sum(1 for v in vals if v == -1) / n * 100
            return round(pos - neg, 2)

        b = {f"p{i}": bal(f"p{i}") for i in range(1, 6)}
        result[city] = {
            "n": n,
            "icc": round((b["p1"]+b["p2"]+b["p3"]+b["p4"]+b["p5"]) / 5, 2),
            "ice": round((b["p1"]+b["p2"]) / 2, 2),
            "iec": round((b["p3"]+b["p4"]+b["p5"]) / 3, 2),
            "balances": b,
        }
    return result


def _n(m):
    return m.get("n_valid") or m.get("n") or "?"


def print_city_table(city_data):
    if not city_data:
        return
    print(f"\n  {'Ciudad':<15} {'ICC':>7} {'ICE':>7} {'IEC':>7} {'Spread':>8}  n")
    for city, m in city_data.items():
        if not m:
            continue
        spread = round(m["iec"] - m["ice"], 1)
        print(f"  {city:<15} {m['icc']:>+7.1f} {m['ice']:>+7.1f} {m['iec']:>+7.1f} {spread:>+8.1f}  {_n(m)}")


def print_strata_table(strata_data):
    if not strata_data:
        return
    print(f"\n  {'Estrato':<10} {'ICC':>7} {'ICE':>7} {'IEC':>7} {'Spread':>8}  n")
    for s, m in sorted(strata_data.items()):
        if not m:
            continue
        spread = round(m["iec"] - m["ice"], 1)
        print(f"  E-{s:<8} {m['icc']:>+7.1f} {m['ice']:>+7.1f} {m['iec']:>+7.1f} {spread:>+8.1f}  {_n(m)}")


def main():
    parser = argparse.ArgumentParser(description="Puntuador EOC — sintético vs real")
    parser.add_argument("--predictions", nargs="+", required=True,
                        help="Archivos JSON de arnes_anclaje.py")
    parser.add_argument("--actuals",     required=True, help="actuals_sellados.json")
    parser.add_argument("--out",         required=True, help="Archivo de salida JSON")
    args = parser.parse_args()

    with open(args.actuals) as f:
        actuals = json.load(f)

    comparisons = []

    for pred_file in sorted(args.predictions):
        with open(pred_file) as f:
            pred = json.load(f)

        month_key  = pred["month_key"]
        month_name = pred["month_name"]
        model      = pred["model"]
        actual     = actuals.get(month_key)

        if not actual:
            print(f"  Sin actual para {month_key}, omitiendo")
            continue

        agg = pred.get("aggregate") or (pred["runs"][0]["metrics"] if pred.get("runs") else None)
        if not agg:
            print(f"  Sin métricas en {pred_file}, omitiendo")
            continue

        pred_icc = agg.get("icc") or agg.get("mean_icc")
        pred_ice = agg.get("ice")
        pred_iec = agg.get("iec")

        actual_icc = actual.get("icc")
        actual_ice = actual.get("ice")
        actual_iec = actual.get("iec")

        # ICE/IEC spread analysis
        synth_spread  = round(pred_iec - pred_ice, 2) if None not in (pred_ice, pred_iec) else None
        actual_spread = round(actual_iec - actual_ice, 2) if None not in (actual_ice, actual_iec) else None
        ratio         = spread_ratio(pred_ice, pred_iec, actual_ice, actual_iec)

        # City and strata breakdown — read directly from run data
        first_run = pred["runs"][0] if pred.get("runs") else {}
        cities    = first_run.get("by_city", {})
        strata    = first_run.get("by_strata", {})

        errors = {}
        if actual_icc is not None and pred_icc is not None:
            errors["icc_mae"] = round(mae(pred_icc, actual_icc), 2)
        if actual_ice is not None and pred_ice is not None:
            errors["ice_mae"] = round(mae(pred_ice, actual_ice), 2)
        if actual_iec is not None and pred_iec is not None:
            errors["iec_mae"] = round(mae(pred_iec, actual_iec), 2)

        print(f"\n{'─'*60}")
        print(f"  {month_name.upper()}  |  {model}")
        print(f"{'─'*60}")
        print(f"  {'':15} {'ICC':>7} {'ICE':>7} {'IEC':>7} {'Spread':>8}")
        print(f"  {'Sintético':<15} {pred_icc or 0:>+7.1f} {pred_ice or 0:>+7.1f} {pred_iec or 0:>+7.1f} {synth_spread or 0:>+8.1f}")
        if actual_icc is not None:
            print(f"  {'Real':<15} {actual_icc:>+7.1f} {actual_ice or 0:>+7.1f} {actual_iec or 0:>+7.1f} {actual_spread or 0:>+8.1f}")
            print(f"  {'Error':<15} {errors.get('icc_mae','—'):>7} {errors.get('ice_mae','—'):>7} {errors.get('iec_mae','—'):>7}  ratio×{ratio or '—'}")

        if cities:
            print(f"\n  Por ciudad:")
            print_city_table(cities)
        if strata:
            print(f"\n  Por estrato:")
            print_strata_table(strata)

        entry = {
            "month_key":    month_key,
            "month_name":   month_name,
            "model":        model,
            "predicted":    {"icc": pred_icc, "ice": pred_ice, "iec": pred_iec},
            "actual":       {"icc": actual_icc, "ice": actual_ice, "iec": actual_iec},
            "errors":       errors,
            "spread": {
                "synthetic":    synth_spread,
                "actual":       actual_spread,
                "ratio":        ratio,
            },
            "by_city":      cities,
            "by_strata":    strata,
        }
        comparisons.append(entry)

    # ── Aggregate summary ──────────────────────────────────────
    icc_maes  = [c["errors"]["icc_mae"] for c in comparisons if "icc_mae" in c["errors"]]
    pred_iccs = [c["predicted"]["icc"]  for c in comparisons if c["predicted"]["icc"] is not None]
    act_iccs  = [c["actual"]["icc"]     for c in comparisons if c["actual"]["icc"]    is not None]
    ratios    = [c["spread"]["ratio"]   for c in comparisons if c["spread"]["ratio"]  is not None]

    n = min(len(pred_iccs), len(act_iccs))
    summary = {
        "n_months":            len(comparisons),
        "mean_icc_mae":        round(sum(icc_maes) / len(icc_maes), 2) if icc_maes else None,
        "rmse_icc":            round(rmse(pred_iccs[:n], act_iccs[:n]), 2) if n >= 2 else None,
        "pearson_icc":         pearson(pred_iccs[:n], act_iccs[:n]) if n >= 2 else None,
        "mean_spread_ratio":   round(sum(ratios) / len(ratios), 2) if ratios else None,
        "min_spread_ratio":    round(min(ratios), 2) if ratios else None,
        "max_spread_ratio":    round(max(ratios), 2) if ratios else None,
    }

    # Spread ratio per month table
    print(f"\n{'═'*60}")
    print("  RESUMEN — Spread ICE/IEC por mes")
    print(f"{'═'*60}")
    print(f"  {'Mes':<20} {'SynthSpread':>12} {'RealSpread':>11} {'Ratio×':>8}")
    for c in comparisons:
        sp = c["spread"]
        ss = f"{sp['synthetic']:+.1f}" if sp['synthetic'] is not None else "—"
        rs = f"{sp['actual']:+.1f}"   if sp['actual']    is not None else "—"
        rt = f"{sp['ratio']:.2f}×"    if sp['ratio']     is not None else "—"
        print(f"  {c['month_name']:<20} {ss:>12} {rs:>11} {rt:>8}")

    print(f"\n  MAE ICC medio  : {summary['mean_icc_mae']}")
    print(f"  RMSE ICC       : {summary['rmse_icc']}")
    print(f"  Pearson ICC    : {summary['pearson_icc']}")
    print(f"  Spread ratio   : {summary['mean_spread_ratio']}× (min {summary['min_spread_ratio']}×, max {summary['max_spread_ratio']}×)")

    output = {
        "timestamp":   datetime.utcnow().isoformat() + "Z",
        "summary":     summary,
        "comparisons": comparisons,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nGuardado → {args.out}")


if __name__ == "__main__":
    main()
