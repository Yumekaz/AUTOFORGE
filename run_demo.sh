#!/usr/bin/env bash
set -euo pipefail

echo "AUTOFORGE - Round 2 Demo"
echo "Note: This script is for Linux/Mac bash. Windows users should run commands manually."

STUB_PID=""
cleanup() {
  if [[ -n "${STUB_PID}" ]] && kill -0 "${STUB_PID}" 2>/dev/null; then
    kill "${STUB_PID}" 2>/dev/null || true
    wait "${STUB_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# 2) Install dependencies
pip install -r requirements.txt -q

# Keep CLI output stable across terminals.
export PYTHONIOENCODING="utf-8"

# 3) Run mock pipeline
python main.py --demo bms --mock --plain

# Ensure replay seed exists (aligned with scripts/run_fallback_mode.py behavior).
if [[ ! -f "output/replay_seed.json" ]]; then
  mkdir -p output
  cat > output/replay_seed.json << 'JSON'
[
  {
    "signals": {
      "vehicle_speed": 30.0,
      "battery_soc": 18.0,
      "battery_temperature": 48.0,
      "tire_pressure_fl": 2.4,
      "tire_pressure_fr": 2.4,
      "tire_pressure_rl": 2.3,
      "tire_pressure_rr": 2.3
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
      "tire_pressure_rr": 2.4
    }
  }
]
JSON
fi

# 4) Start REST stub in background
python integrations/service_stub/rest_bms_service.py &
STUB_PID=$!

# 5) Wait 2 seconds
sleep 2

# 6) Run CARLA replay
python integrations/carla_bridge/carla_integration.py \
  --mode replay \
  --replay-input output/replay_seed.json \
  --service-url http://localhost:30509 \
  --log-path output/carla_replay_validation.json \
  --max-samples 20

# 7) Run ML inference on CARLA stress data
python scripts/ml_infer_carla.py \
  --model models/tire_failure.onnx \
  --csv input/vehicle_data_carla_stress.csv \
  --out-json output/ml/carla_inference_stress_summary.json

# 8) Print output summary
echo ""
echo "Output summary:"
check_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    echo "  [OK] $path"
  else
    echo "  [MISSING] $path"
  fi
}

check_file "output/BMSDiagnosticService/trace.yaml"
check_file "output/carla_replay_validation.json"
check_file "output/ml/carla_inference_stress_summary.json"
check_file "output/ml/carla_inference_predictions.csv"

# 9) Kill stub (also enforced by trap)
cleanup
STUB_PID=""
echo "Demo run complete."
