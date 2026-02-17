#!/usr/bin/env python3
"""
Run AUTOFORGE end-to-end with live CARLA integration (no replay).

This script will:
1) Build fallback CSV (kept for ML path consistency)
2) Train ONNX model
3) Generate SOME/IP config
4) Run core pipeline with Ollama
5) Optionally run Gemini if GOOGLE_API_KEY is set
6) Run Java and Kotlin requirement variants
7) Start local REST stub
8) Run CARLA bridge in live mode using Python 3.7 env (required by CARLA 0.9.13 wheel)
9) Verify key artifacts
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
DEFAULT_CARLA_PY = ROOT / ".venv37" / "Scripts" / "python.exe"


def run(cmd: list[str], env: dict[str, str] | None = None) -> None:
    print(f"[RUN] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AUTOFORGE end-to-end with live CARLA")
    parser.add_argument("--provider", default="ollama", choices=["ollama", "gemini"])
    parser.add_argument("--max-samples", type=int, default=200, help="CARLA live samples")
    parser.add_argument("--rate-hz", type=float, default=10.0, help="CARLA sample rate")
    parser.add_argument("--carla-python", default=str(DEFAULT_CARLA_PY), help="Python executable for CARLA bridge")
    parser.add_argument("--skip-gemini", action="store_true", help="Skip Gemini run even when GOOGLE_API_KEY exists")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONWARNINGS", "ignore::FutureWarning")

    carla_py = Path(args.carla_python)
    if not carla_py.exists():
        print(f"[ERROR] CARLA Python executable not found: {carla_py}")
        print("[HINT] Create .venv37 and install carla wheel for 0.9.13, then rerun.")
        return 1

    # 1) Public-data fallback CSV for ML reproducibility
    run([PY, "scripts/prepare_public_vehicle_data.py"], env=env)

    # 2) ML ONNX training
    run([PY, "src/ml/train.py", "--csv", "input/vehicle_data.csv", "--output", "models/tire_failure.onnx"], env=env)

    # 3) SOME/IP config
    run(
        [
            PY,
            "src/codegen/protocol_adapter.py",
            "--requirement",
            "input/requirements/bms_diagnostic.yaml",
            "--output",
            "output/someip_service.json",
        ],
        env=env,
    )

    # 4) Core run
    run([PY, "main.py", "--plain", "--demo", "bms", "--provider", args.provider], env=env)

    # 5) Optional Gemini run
    if not args.skip_gemini and env.get("GOOGLE_API_KEY"):
        run([PY, "main.py", "--plain", "--demo", "bms", "--provider", "gemini"], env=env)
    elif not args.skip_gemini:
        print("[INFO] GOOGLE_API_KEY not set. Skipping Gemini run.")

    # 6) Java + Kotlin runs
    run(
        [PY, "main.py", "--plain", "--requirement", "input/requirements/bms_diagnostic_java.yaml", "--provider", args.provider],
        env=env,
    )
    run(
        [PY, "main.py", "--plain", "--requirement", "input/requirements/bms_diagnostic_kotlin.yaml", "--provider", args.provider],
        env=env,
    )

    # 7) Start local stub + 8) run live CARLA bridge
    stub = subprocess.Popen([PY, "integrations/service_stub/rest_bms_service.py"], cwd=ROOT, env=env)
    try:
        time.sleep(1.5)
        run(
            [
                str(carla_py),
                "integrations/carla_bridge/carla_integration.py",
                "--mode",
                "live",
                "--host",
                "localhost",
                "--port",
                "2000",
                "--service-url",
                "http://localhost:30509",
                "--log-path",
                "output/carla_live_validation.json",
                "--max-samples",
                str(args.max_samples),
                "--rate-hz",
                str(args.rate_hz),
            ],
            env=env,
        )
    finally:
        stub.terminate()
        try:
            stub.wait(timeout=5)
        except subprocess.TimeoutExpired:
            stub.kill()

    # 9) Artifact checks
    required = [
        ROOT / "output" / "someip_service.json",
        ROOT / "models" / "tire_failure.onnx",
        ROOT / "output" / "carla_live_validation.json",
        ROOT / "output" / "BMSDiagnosticService" / "trace.yaml",
        ROOT / "output" / "BMSDiagnosticServiceJava" / "bmsdiagnosticservicejava.java",
        ROOT / "output" / "BMSDiagnosticServiceKotlin" / "bmsdiagnosticservicekotlin.kt",
        ROOT / "output" / "BMSDiagnosticServiceKotlin" / "BMSDiagnosticServiceKotlin.java",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("[ERROR] Missing required artifacts:")
        for item in missing:
            print(f"  - {item}")
        return 1

    print("[OK] Live mode pipeline completed with required artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
