#!/usr/bin/env python3
"""
Convert CARLA live validation JSON to ML-ready CSV.

Input:
- output/carla_live_validation.json

Output columns (compatible with src/ml/train.py):
- tire_pressure_fl
- tire_pressure_fr
- tire_pressure_rl
- tire_pressure_rr
- vehicle_speed_kmh
- ambient_temperature_c
- failure_score
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _failure_score(sig: Dict[str, Any]) -> float:
    """
    Rule-based supervised label:
    - low tire pressure and high battery temp increase risk
    - high speed amplifies risk
    """
    tires = [
        _to_float(sig.get("tire_pressure_fl"), 2.5),
        _to_float(sig.get("tire_pressure_fr"), 2.5),
        _to_float(sig.get("tire_pressure_rl"), 2.4),
        _to_float(sig.get("tire_pressure_rr"), 2.4),
    ]
    speed = _to_float(sig.get("vehicle_speed"), 0.0)
    batt_temp = _to_float(sig.get("battery_temperature"), 25.0)

    pressure_deficit = max(0.0, 2.4 - min(tires)) / 0.8
    temp_risk = max(0.0, batt_temp - 45.0) / 25.0
    speed_factor = min(speed / 140.0, 1.0)

    score = 0.5 * pressure_deficit + 0.35 * temp_risk + 0.15 * speed_factor
    return round(max(0.0, min(1.0, score)), 6)


def convert(log_path: Path) -> pd.DataFrame:
    payload = json.loads(log_path.read_text())
    records = payload.get("records", [])
    rows: List[Dict[str, float]] = []

    for rec in records:
        sig = rec.get("signals", {})
        speed = _to_float(sig.get("vehicle_speed"), 0.0)
        battery_temp = _to_float(sig.get("battery_temperature"), 25.0)
        ambient = _to_float(sig.get("ambient_temperature"), battery_temp - 8.0)

        rows.append(
            {
                "tire_pressure_fl": _to_float(sig.get("tire_pressure_fl"), 2.5),
                "tire_pressure_fr": _to_float(sig.get("tire_pressure_fr"), 2.5),
                "tire_pressure_rl": _to_float(sig.get("tire_pressure_rl"), 2.4),
                "tire_pressure_rr": _to_float(sig.get("tire_pressure_rr"), 2.4),
                "vehicle_speed_kmh": speed,
                "ambient_temperature_c": ambient,
                "failure_score": _failure_score(sig),
            }
        )

    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert CARLA live JSON log to ML CSV")
    parser.add_argument("--input", default="output/carla_live_validation.json")
    parser.add_argument("--output", default="input/vehicle_data_carla.csv")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input log not found: {input_path}")

    df = convert(input_path)
    if df.empty:
        raise RuntimeError("No records found in CARLA log")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"[CARLA-CSV] Input log: {input_path}")
    print(f"[CARLA-CSV] Rows: {len(df)}")
    print(f"[CARLA-CSV] Output: {output_path}")
    print(
        f"[CARLA-CSV] failure_score range: {df['failure_score'].min():.6f} .. {df['failure_score'].max():.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
