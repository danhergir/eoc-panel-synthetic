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

        month_key = pred["month_key"]
        model     = pred["model"]
        actual    = actuals.get(month_key)

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

        errors = {}
        if actual.get("icc") is not None and pred_icc is not None:
            errors["icc_mae"] = round(mae(pred_icc, actual["icc"]), 2)
        if actual.get("ice") is not None and pred_ice is not None:
            errors["ice_mae"] = round(mae(pred_ice, actual["ice"]), 2)
        if actual.get("iec") is not None and pred_iec is not None:
            errors["iec_mae"] = round(mae(pred_iec, actual["iec"]), 2)

        entry = {
            "month_key":  month_key,
            "month_name": pred["month_name"],
            "model":      model,
            "predicted":  {"icc": pred_icc, "ice": pred_ice, "iec": pred_iec},
            "actual":     {"icc": actual.get("icc"), "ice": actual.get("ice"), "iec": actual.get("iec")},
            "errors":     errors,
        }
        comparisons.append(entry)

        icc_err = errors.get("icc_mae", "N/A")
        print(f"  {month_key} | {model:30s} | pred={pred_icc:+.1f}  actual={actual['icc']:+.1f}  MAE={icc_err}")

    # Aggregate
    icc_maes = [c["errors"]["icc_mae"]    for c in comparisons if "icc_mae" in c["errors"]]
    pred_iccs = [c["predicted"]["icc"]    for c in comparisons if c["predicted"]["icc"] is not None]
    act_iccs  = [c["actual"]["icc"]       for c in comparisons if c["actual"]["icc"]    is not None]

    n = min(len(pred_iccs), len(act_iccs))
    summary = {
        "n_months":     len(comparisons),
        "mean_icc_mae": round(sum(icc_maes) / len(icc_maes), 2) if icc_maes else None,
        "rmse_icc":     round(rmse(pred_iccs[:n], act_iccs[:n]), 2) if n >= 2 else None,
        "pearson_icc":  pearson(pred_iccs[:n], act_iccs[:n]) if n >= 2 else None,
    }

    output = {
        "timestamp":   datetime.utcnow().isoformat() + "Z",
        "summary":     summary,
        "comparisons": comparisons,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResumen:")
    print(f"  MAE ICC medio : {summary['mean_icc_mae']}")
    print(f"  RMSE ICC      : {summary['rmse_icc']}")
    print(f"  Pearson ICC   : {summary['pearson_icc']}")
    print(f"\nGuardado → {args.out}")


if __name__ == "__main__":
    main()
