#!/usr/bin/env python3
"""
Generate bar-scale synthetic training CSV for tire failure model.

Schema matches src/ml/train.py requirements:
- tire_pressure_fl/fr/rl/rr
- vehicle_speed_kmh
- ambient_temperature_c
- failure_score
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def _score(
    fl: np.ndarray,
    fr: np.ndarray,
    rl: np.ndarray,
    rr: np.ndarray,
    speed: np.ndarray,
    temp: np.ndarray,
) -> np.ndarray:
    min_tire = np.minimum(np.minimum(fl, fr), np.minimum(rl, rr))
    pressure_risk = np.clip((2.5 - min_tire) / 1.1, 0.0, 1.0)
    speed_risk = np.clip(speed / 140.0, 0.0, 1.0)
    temp_risk = np.clip((temp - 35.0) / 20.0, 0.0, 1.0)
    score = 0.65 * pressure_risk + 0.25 * speed_risk + 0.10 * temp_risk
    return np.clip(score, 0.0, 1.0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate bar-scale synthetic training data")
    parser.add_argument("--rows", type=int, default=200000)
    parser.add_argument("--degraded-ratio", type=float, default=0.2)
    parser.add_argument("--output", default="input/vehicle_data_bar_synth.csv")
    args = parser.parse_args()

    if args.rows <= 0:
        raise ValueError("--rows must be > 0")
    if not (0.0 < args.degraded_ratio < 1.0):
        raise ValueError("--degraded-ratio must be in (0,1)")

    rng = np.random.default_rng(42)
    n = args.rows
    k = int(round(n * args.degraded_ratio))

    # Healthy baseline around nominal bar-scale tires.
    fl = rng.normal(2.50, 0.06, size=n)
    fr = rng.normal(2.50, 0.06, size=n)
    rl = rng.normal(2.40, 0.06, size=n)
    rr = rng.normal(2.40, 0.06, size=n)
    speed = rng.uniform(0, 90, size=n)
    temp = rng.uniform(15, 35, size=n)

    idx = rng.choice(np.arange(n), size=k, replace=False)

    # Inject explicit degraded scenario for 20% rows.
    fl[idx] = rng.uniform(1.6, 1.9, size=k)
    speed[idx] = rng.uniform(80, 130, size=k)
    temp[idx] = rng.uniform(30, 48, size=k)

    fl = np.clip(fl, 1.5, 3.2)
    fr = np.clip(fr, 1.8, 3.2)
    rl = np.clip(rl, 1.8, 3.2)
    rr = np.clip(rr, 1.8, 3.2)

    failure = _score(fl, fr, rl, rr, speed, temp)

    df = pd.DataFrame(
        {
            "tire_pressure_fl": fl,
            "tire_pressure_fr": fr,
            "tire_pressure_rl": rl,
            "tire_pressure_rr": rr,
            "vehicle_speed_kmh": speed,
            "ambient_temperature_c": temp,
            "failure_score": failure,
        }
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    healthy = df["tire_pressure_fl"] >= 2.2
    degraded = (df["tire_pressure_fl"] <= 1.9) & (df["vehicle_speed_kmh"] > 80)
    print(f"[BAR-DATA] Wrote: {out} rows={len(df)}")
    print(f"[BAR-DATA] degraded rows: {int(degraded.sum())} ({degraded.mean()*100:.2f}%)")
    print(
        f"[BAR-DATA] mean failure healthy={df.loc[healthy, 'failure_score'].mean():.4f} "
        f"degraded={df.loc[degraded, 'failure_score'].mean():.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
