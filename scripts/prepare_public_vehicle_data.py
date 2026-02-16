#!/usr/bin/env python3
"""
Prepare AUTOFORGE ML CSV from a public OBD-II dataset (secondary fallback path).

This script maps public telemetry CSV files to AUTOFORGE's required schema:
  - tire_pressure_fl
  - tire_pressure_fr
  - tire_pressure_rl
  - tire_pressure_rr
  - vehicle_speed_kmh
  - ambient_temperature_c
  - failure_score

Notes:
- The source dataset does not contain direct tire-pressure or failure labels.
- Tire pressures and failure score are engineered proxies derived from public
  telemetry signals. This must be disclosed in competition evidence as
  "public mapped fallback", not CARLA/live telemetry.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd


def _pick_column(columns: List[str], token: str) -> str:
    token_lower = token.lower()
    for col in columns:
        if token_lower in col.lower():
            return col
    raise KeyError(f"Could not find column containing token: {token}")


def _load_public_obd_csvs(input_dir: Path) -> pd.DataFrame:
    csv_files = sorted(input_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {input_dir}")

    frames = []
    for csv_path in csv_files:
        df = pd.read_csv(csv_path)
        frames.append(df)

    merged = pd.concat(frames, ignore_index=True)
    return merged


def _build_autoforge_schema(raw: pd.DataFrame) -> pd.DataFrame:
    cols = list(raw.columns)

    speed_col = _pick_column(cols, "Vehicle Speed Sensor")
    ambient_col = _pick_column(cols, "Ambient Air Temperature")
    map_col = _pick_column(cols, "Intake Manifold Absolute Pressure")
    coolant_col = _pick_column(cols, "Engine Coolant Temperature")
    pedal_col = _pick_column(cols, "Accelerator Pedal Position D")

    data = pd.DataFrame(
        {
            "vehicle_speed_kmh": pd.to_numeric(raw[speed_col], errors="coerce"),
            "ambient_temperature_c": pd.to_numeric(raw[ambient_col], errors="coerce"),
            "map_kpa": pd.to_numeric(raw[map_col], errors="coerce"),
            "coolant_c": pd.to_numeric(raw[coolant_col], errors="coerce"),
            "pedal_pct": pd.to_numeric(raw[pedal_col], errors="coerce"),
        }
    )

    # Fill sparse telemetry gaps.
    data = data.interpolate(limit_direction="both")
    data = data.bfill().ffill()
    data = data.dropna()

    # Keep physically plausible range.
    data = data[(data["vehicle_speed_kmh"] >= 0) & (data["vehicle_speed_kmh"] <= 220)]
    data = data[(data["ambient_temperature_c"] >= -30) & (data["ambient_temperature_c"] <= 60)]

    # Engineer tire-pressure proxies from load/temperature/speed effects.
    # Baseline 32 psi with deterministic variations.
    speed_factor = (data["vehicle_speed_kmh"] / 180.0) * 1.8
    temp_factor = ((data["ambient_temperature_c"] - 20.0) / 40.0) * 1.0
    map_factor = ((data["map_kpa"] - 100.0) / 60.0) * 0.8
    coolant_factor = ((data["coolant_c"] - 90.0) / 50.0) * 0.4
    pedal_factor = (data["pedal_pct"] / 100.0) * 0.8

    base = 32.0 - speed_factor + temp_factor - map_factor - coolant_factor - pedal_factor

    out = pd.DataFrame()
    out["tire_pressure_fl"] = np.clip(base + 0.20, 24.0, 40.0)
    out["tire_pressure_fr"] = np.clip(base - 0.10, 24.0, 40.0)
    out["tire_pressure_rl"] = np.clip(base - 0.35, 24.0, 40.0)
    out["tire_pressure_rr"] = np.clip(base - 0.25, 24.0, 40.0)
    out["vehicle_speed_kmh"] = data["vehicle_speed_kmh"].astype(float)
    out["ambient_temperature_c"] = data["ambient_temperature_c"].astype(float)

    # Engineer a bounded failure score proxy.
    pressure_dev = (
        np.abs(out["tire_pressure_fl"] - 32.0)
        + np.abs(out["tire_pressure_fr"] - 32.0)
        + np.abs(out["tire_pressure_rl"] - 32.0)
        + np.abs(out["tire_pressure_rr"] - 32.0)
    ) / 4.0
    speed_risk = out["vehicle_speed_kmh"] / 180.0
    temp_risk = np.abs(out["ambient_temperature_c"] - 22.0) / 40.0
    out["failure_score"] = np.clip(0.14 * pressure_dev + 0.25 * speed_risk + 0.12 * temp_risk, 0.0, 1.0)

    return out.reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare AUTOFORGE ML CSV from public OBD-II data")
    parser.add_argument(
        "--input-dir",
        default="data/public/Automotive_Diagnostics/OBD-II-Dataset",
        help="Directory containing source public OBD CSV files",
    )
    parser.add_argument(
        "--output-csv",
        default="input/vehicle_data.csv",
        help="Output CSV path in AUTOFORGE schema",
    )
    parser.add_argument(
        "--meta-out",
        default="output/public_dataset_mapping_meta.json",
        help="Metadata JSON describing source and mapping",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=200000,
        help="Maximum output rows (deterministic sample). 0 keeps all rows.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_csv = Path(args.output_csv)
    meta_out = Path(args.meta_out)

    raw = _load_public_obd_csvs(input_dir)
    mapped = _build_autoforge_schema(raw)
    rows_before_cap = len(mapped)
    if args.max_rows and len(mapped) > args.max_rows:
        mapped = mapped.sample(n=args.max_rows, random_state=42).sort_index().reset_index(drop=True)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    mapped.to_csv(output_csv, index=False)

    meta = {
        "source": "public",
        "source_dataset": "Automotive_Diagnostics (OBD-II-Dataset)",
        "source_path": str(input_dir),
        "output_csv": str(output_csv),
        "rows": int(len(mapped)),
        "rows_before_cap": int(rows_before_cap),
        "columns": list(mapped.columns),
        "notes": [
            "Secondary fallback path when CARLA live telemetry is unavailable.",
            "Tire pressure and failure_score are engineered proxies from public OBD signals.",
            "Must be labeled as public mapped fallback in reports/slides.",
        ],
    }
    meta_out.parent.mkdir(parents=True, exist_ok=True)
    meta_out.write_text(json.dumps(meta, indent=2))

    print(f"[DATA] Wrote mapped fallback CSV: {output_csv} ({len(mapped)} rows)")
    print(f"[DATA] Wrote mapping metadata: {meta_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
