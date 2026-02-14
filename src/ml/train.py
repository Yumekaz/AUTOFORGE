"""
AUTOFORGE ML Training Pipeline

Trains a tire-failure regression model using CSV vehicle data (or synthetic data),
then exports the model to ONNX.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import numpy as np


def _load_or_generate_data(csv_path: Optional[Path], rows: int = 1000):
    """Load training data from CSV or generate deterministic synthetic data."""
    if csv_path and csv_path.exists():
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("pandas is required for CSV input mode") from exc

        df = pd.read_csv(csv_path)
        required = [
            "tire_pressure_fl",
            "tire_pressure_fr",
            "tire_pressure_rl",
            "tire_pressure_rr",
            "vehicle_speed_kmh",
            "ambient_temperature_c",
            "failure_score",
        ]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        x = df[
            [
                "tire_pressure_fl",
                "tire_pressure_fr",
                "tire_pressure_rl",
                "tire_pressure_rr",
                "vehicle_speed_kmh",
                "ambient_temperature_c",
            ]
        ].to_numpy(dtype=np.float32)
        y = df["failure_score"].to_numpy(dtype=np.float32)
        return x, y

    # Synthetic fallback for no-data environments
    rng = np.random.default_rng(42)
    tire = rng.normal(loc=32.0, scale=2.0, size=(rows, 4)).astype(np.float32)
    speed = rng.uniform(0, 140, size=(rows, 1)).astype(np.float32)
    temp = rng.uniform(-10, 45, size=(rows, 1)).astype(np.float32)
    x = np.concatenate([tire, speed, temp], axis=1)

    # Higher risk when pressure drops away from nominal and speed is high
    pressure_penalty = np.abs(tire - 32.0).mean(axis=1)
    speed_factor = (speed[:, 0] / 140.0) * 0.25
    y = np.clip(0.15 * pressure_penalty + speed_factor, 0.0, 1.0).astype(np.float32)
    return x, y


def train_and_export(csv_path: Optional[Path], output_model: Path) -> Path:
    """Train sklearn model and export ONNX model."""
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error
    except ImportError as exc:
        raise RuntimeError("scikit-learn is required for training") from exc

    x, y = _load_or_generate_data(csv_path)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x_train, y_train)
    preds = model.predict(x_test)
    mse = mean_squared_error(y_test, preds)

    print(f"[ML] Training samples: {len(x_train)}")
    print(f"[ML] Test samples: {len(x_test)}")
    print(f"[ML] MSE: {mse:.6f}")

    # Export to ONNX
    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
    except ImportError as exc:
        raise RuntimeError("skl2onnx is required for ONNX export") from exc

    initial_type = [("tire_signals", FloatTensorType([None, 6]))]
    onnx_model = convert_sklearn(model, initial_types=initial_type)

    output_model.parent.mkdir(parents=True, exist_ok=True)
    with open(output_model, "wb") as f:
        f.write(onnx_model.SerializeToString())

    print(f"[ML] Exported ONNX model: {output_model}")
    return output_model


def main() -> int:
    parser = argparse.ArgumentParser(description="Train tire-failure model and export ONNX")
    parser.add_argument("--csv", type=str, default="", help="Input CSV file")
    parser.add_argument("--output", type=str, default="models/tire_failure.onnx")
    args = parser.parse_args()

    csv_path = Path(args.csv) if args.csv else None
    output_model = Path(args.output)
    train_and_export(csv_path, output_model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

