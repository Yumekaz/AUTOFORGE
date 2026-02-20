#!/usr/bin/env python3
"""
Run AUTOFORGE end-to-end in fallback mode (no live CARLA required).

This script is intended for competition-safe local execution when CARLA live mode
is unavailable. It will:
1) Build public-data fallback CSV for ML
2) Train ONNX model from fallback CSV
3) Generate SOME/IP config artifact
4) Run core pipeline with Ollama
5) Optionally run Gemini if GOOGLE_API_KEY is set
6) Run Java and Kotlin requirements (including Java companion)
7) Start local REST stub and execute CARLA bridge in replay mode
8) Verify key artifacts exist
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import shutil
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(cmd: list[str], env: dict[str, str] | None = None) -> None:
    print(f"[RUN] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def ensure_replay_seed(path: Path) -> None:
    if path.exists():
        return
    seed = [
        {
            "signals": {
                "vehicle_speed": 30.0,
                "battery_soc": 18.0,
                "battery_temperature": 48.0,
                "tire_pressure_fl": 2.4,
                "tire_pressure_fr": 2.4,
                "tire_pressure_rl": 2.3,
                "tire_pressure_rr": 2.3,
            }
        },
        {
            "signals": {
                "vehicle_speed": 55.0,
                "battery_soc": 65.0,
                "battery_temperature": 30.0,
                "tire_pressure_fl": 2.5,
                "tire_pressure_fr": 2.5,
                "tire_pressure_rl": 2.4,
                "tire_pressure_rr": 2.4,
            }
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(seed, indent=2))


def main() -> int:
    load_dotenv(ROOT / ".env")
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONWARNINGS", "ignore::FutureWarning")

    # 1) Public-data fallback CSV
    run([PY, "scripts/prepare_public_vehicle_data.py"], env=env)

    # 2) ML ONNX training from fallback CSV
    run([PY, "src/ml/train.py", "--csv", "input/vehicle_data.csv", "--output", "models/tire_failure_bar.onnx"], env=env)
    # Backward-compatible publish path for existing consumers.
    shutil.copyfile(ROOT / "models" / "tire_failure_bar.onnx", ROOT / "models" / "tire_failure.onnx")
    print("[ML] Published compatibility model: models/tire_failure.onnx")

    # 3) SOME/IP config generator
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

    # 4) Core Ollama run
    run([PY, "main.py", "--plain", "--demo", "bms", "--provider", "ollama"], env=env)

    # 5) Optional Gemini run
    if env.get("GOOGLE_API_KEY"):
        run([PY, "main.py", "--plain", "--demo", "bms", "--provider", "gemini"], env=env)
    else:
        print("[INFO] GOOGLE_API_KEY not set. Skipping Gemini run.")

    # 6) Java + Kotlin runs
    run(
        [PY, "main.py", "--plain", "--requirement", "input/requirements/bms_diagnostic_java.yaml", "--provider", "ollama"],
        env=env,
    )
    run(
        [PY, "main.py", "--plain", "--requirement", "input/requirements/bms_diagnostic_kotlin.yaml", "--provider", "ollama"],
        env=env,
    )

    # 7) Replay mode with local REST stub
    replay_seed = ROOT / "output" / "replay_seed.json"
    ensure_replay_seed(replay_seed)

    stub = subprocess.Popen([PY, "integrations/service_stub/rest_bms_service.py"], cwd=ROOT, env=env)
    try:
        time.sleep(1.5)
        run(
            [
                PY,
                "integrations/carla_bridge/carla_integration.py",
                "--mode",
                "replay",
                "--replay-input",
                "output/replay_seed.json",
                "--service-url",
                "http://localhost:30509",
                "--log-path",
                "output/carla_replay_validation.json",
                "--max-samples",
                "2",
                "--rate-hz",
                "20",
            ],
            env=env,
        )
    finally:
        stub.terminate()
        try:
            stub.wait(timeout=5)
        except subprocess.TimeoutExpired:
            stub.kill()

    # 8) Artifact checks
    required = [
        ROOT / "output" / "someip_service.json",
        ROOT / "models" / "tire_failure.onnx",
        ROOT / "output" / "public_dataset_mapping_meta.json",
        ROOT / "output" / "carla_replay_validation.json",
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

    print("[OK] Fallback mode pipeline completed with required artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
