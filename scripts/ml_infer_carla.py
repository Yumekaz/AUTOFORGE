#!/usr/bin/env python3
"""
Run ONNX inference on CARLA CSV and export per-sample predictions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


FEATURES = [
    "tire_pressure_fl",
    "tire_pressure_fr",
    "tire_pressure_rl",
    "tire_pressure_rr",
    "vehicle_speed_kmh",
    "ambient_temperature_c",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ONNX inference on CARLA CSV")
    parser.add_argument("--model", default="models/tire_failure_bar.onnx")
    parser.add_argument("--csv", default="input/vehicle_data_carla.csv")
    parser.add_argument("--out-csv", default="output/ml/carla_inference_predictions.csv")
    parser.add_argument("--out-json", default="output/ml/carla_inference_summary.json")
    args = parser.parse_args()

    try:
        import onnxruntime as ort
    except ImportError as exc:
        raise RuntimeError("onnxruntime is required for inference") from exc

    model_path = Path(args.model)
    csv_path = Path(args.csv)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    x = df[FEATURES].to_numpy(dtype=np.float32)

    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    in_name = session.get_inputs()[0].name
    out_name = session.get_outputs()[0].name
    preds = session.run([out_name], {in_name: x})[0].reshape(-1)

    out_df = df.copy()
    out_df["predicted_failure_score"] = preds.astype(np.float32)

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_csv, index=False)

    summary = {
        "model": str(model_path),
        "input_csv": str(csv_path),
        "samples": int(len(out_df)),
        "pred_min": float(np.min(preds)),
        "pred_max": float(np.max(preds)),
        "pred_mean": float(np.mean(preds)),
        "output_csv": str(out_csv),
    }
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2))

    print(f"[INFER] Samples: {summary['samples']}")
    print(f"[INFER] Pred range: {summary['pred_min']:.6f} .. {summary['pred_max']:.6f}")
    print(f"[INFER] Pred mean: {summary['pred_mean']:.6f}")
    print(f"[INFER] Saved predictions: {out_csv}")
    print(f"[INFER] Saved summary: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
