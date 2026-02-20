# COMMANDS

## Environment Setup

```powershell
cd C:\Users\patha\Desktop\AUTOFORGE
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` in repo root:

```env
GOOGLE_API_KEY=your_key_here
```

## One-Command Runs

Fallback mode (recommended, no live CARLA required):

```powershell
python scripts\run_fallback_mode.py
```

Live CARLA mode (requires CARLA app running + `.venv37` with `carla==0.9.13`):

```powershell
python scripts\run_live_mode.py
```

Useful live options:

```powershell
python scripts\run_live_mode.py --max-samples 300 --rate-hz 10
python scripts\run_live_mode.py --provider gemini
python scripts\run_live_mode.py --carla-python .\.venv37\Scripts\python.exe
python scripts\run_live_mode.py --with-hmi-dashboard --hmi-host 127.0.0.1 --hmi-port 30600
```

Live dashboard URL (when enabled):

```text
http://127.0.0.1:30600
```

## Demo Runs

```powershell
python main.py --plain --demo bms --provider ollama
python main.py --plain --demo bms --provider gemini
```

## Requirement-Specific Runs

```powershell
python main.py --plain --requirement input/requirements/bms_diagnostic_java.yaml --provider ollama
python main.py --plain --requirement input/requirements/bms_diagnostic_kotlin.yaml --provider ollama
python main.py --plain --requirement input/requirements/bms_diagnostic_with_ml.yaml --provider ollama
```

## SOME/IP Generator

```powershell
python src/codegen/protocol_adapter.py --requirement input/requirements/bms_diagnostic.yaml --output output/someip_service.json
```

Protocol abstraction artifacts:

```powershell
python src/codegen/protocol_adapter.py --requirement input/requirements/bms_diagnostic.yaml --output output/someip_service.json --abstraction-dir output/someip_abstraction
```

## ML Train + ONNX Export

```powershell
python src/ml/train.py --csv input/vehicle_data.csv --output models/tire_failure_bar.onnx
```

## Strict Compliance Proof

```powershell
python scripts/verify_strict_cpp_compliance.py
```

Evidence output:

```text
output/strict_cpp_compliance_report.json
```

## Torture Test Evidence

```powershell
python scripts/torture_test.py --provider ollama --runs 20 --output evidence/torture_log.json
```

Quick sanity run:

```powershell
python scripts/torture_test.py --provider ollama --runs 5 --output evidence/torture_log_5.json
```

## Benchmark

```powershell
python scripts/benchmark.py --dry-run
python scripts/benchmark.py --runs 20 --providers gemini,ollama --output benchmark_results.json
```

## Scaffolding Impact Metrics

```powershell
python scripts/scaffolding_impact.py --auto-services
python scripts/scaffolding_impact.py --auto-services --manual-baseline-loc 1000
```

## OTA Delta Evidence (v1.0 -> v1.1)

```powershell
python scripts/generate_ota_delta.py --service BMSDiagnosticService --base-version 1.0.0 --target-version 1.1.0 --base-image autoforge/bms:1.0.0 --target-image autoforge/bms:1.1.0 --base-file output/ota_v1_0.txt --target-file output/ota_v1_1.txt --output-dir output/ota_delta/BMSDiagnosticService_v1.0.0_to_v1.1.0
```

Expected outputs:

```text
delta_manifest.json
delta_chunks.json
verification.json
```

## CARLA Integration Modes

Replay mode:

```powershell
python integrations/carla_bridge/carla_integration.py --mode replay --replay-input output/replay_seed.json --service-url http://localhost:30509 --log-path output/carla_replay_validation.json
```

Live mode:

```powershell
python integrations/carla_bridge/carla_integration.py --mode live --host localhost --port 2000 --service-url http://localhost:30509 --log-path output/carla_live_validation.json
```