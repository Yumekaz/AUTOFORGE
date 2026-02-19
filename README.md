# AUTOFORGE

Adversarial GenAI pipeline for predictable SDV software development (TELIPORT Season 3, Case Study 2).

## Why this project exists

Manual SDV backend/service development is slow and repetitive, especially when you add:
- strict compliance expectations (MISRA, ASPICE-style traceability),
- multi-language targets,
- OTA/variant support,
- test coverage and validation loops.

AUTOFORGE addresses this by using adversarial role separation plus deterministic validation.

## Core architecture

```text
Input Requirement YAML
      |
      v
[AUDITOR AGENT]
Generates strict tests first
      |
      v
[ARCHITECT AGENT]
Generates implementation to satisfy tests
      |
      v
[VALIDATION GATE]
Compile + static checks + test execution + ASIL-style heuristics
      |
   fail/retry  <---- feedback loop with errors
      |
      v
[PACKAGING + EVIDENCE]
Traceability, OTA manifests, protocol config, optional ONNX wrapper
```

## Innovation points (Round-1 idea, Round-2 implementation)

1. Adversarial GenAI governance
- Auditor and Architect are separate role prompts with different behavior.
- Validation is tool-driven, not self-reported by LLM.

2. Test-first generation
- Tests are produced before implementation.
- Retry loop closes failures with explicit error context.

3. Automotive evidence artifacts
- Traceability matrix (CSV/YAML)
- Audit report
- OTA manifest + variant configs
- Protocol adapter config

4. Hybrid analytics path
- Offline supervised ML training and ONNX export.
- C++ ONNX wrapper generation path from requirement metadata.

## What is implemented now

Working:
- Gemini + Ollama pipeline runs
- C++/Java/Kotlin generation (Kotlin + Java companion path)
- SOME/IP config generation
- Protocol Abstraction with SOME/IP code generation (vsomeip skeleton + mapping artifacts)
- OTA + variants (ICE/Hybrid/EV)
- Traceability and audit artifacts
- Public-data fallback ML path (`input/vehicle_data.csv`) + ONNX export
- ONNX wrapper generation via ML-enabled requirement
- Strict C++ compliance proof script with clang-tidy/cppcheck/compile checks
- CARLA replay mode flow (fallback)
- Torture test runner (`20` repeated runs + metrics JSON)

Pending / environment-dependent:
- Live CARLA simulation mode
- CI-gated coverage evidence finalization

## Case Study 2 mapping (honest status)

| Case Study expectation | AUTOFORGE status |
|---|---|
| Requirements -> design/code/tests workflow | Implemented |
| SoA service generation with protocol support | Implemented (SOME/IP focus) |
| OTA/subscription extensibility | Implemented (OTA + variant artifacts) |
| Multi-language generation | Implemented (C++, Java, Kotlin; Rust path exists) |
| Vehicle health diagnostics use case | Implemented |
| Predictive analytics (ML) | Implemented (fallback public dataset path) |
| MISRA / ASPICE-style evidence | Implemented (tool + artifact path) |
| CARLA simulation evidence | Replay implemented; live mode pending runtime |
| LLM comparison/KPI benchmarking | Implemented (benchmark + torture scripts) |

## Quick start

### 1) Environment

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

### 2) One-command fallback run (recommended)

No live CARLA required. This is the practical Round-2 fallback path.

```powershell
python scripts\run_fallback_mode.py
```

It executes:
- fallback public CSV generation,
- ML train/export,
- SOME/IP artifact generation,
- pipeline runs (ollama + gemini if key present),
- Java/Kotlin generation,
- replay-mode CARLA validation with local REST stub,
- artifact presence checks.

### 3) One-command live CARLA run (no replay)

Requires:
- CARLA app already running (`CarlaUE4.exe`)
- `.venv37` present with `carla==0.9.13` wheel installed

```powershell
python scripts\run_live_mode.py
```

Useful options:

```powershell
python scripts\run_live_mode.py --max-samples 300 --rate-hz 10
python scripts\run_live_mode.py --provider gemini
python scripts\run_live_mode.py --carla-python .\.venv37\Scripts\python.exe
python scripts\run_live_mode.py --with-hmi-dashboard --hmi-host 127.0.0.1 --hmi-port 30600
```

Live dashboard URL (when enabled):
- `http://127.0.0.1:30600`

## Core commands

### Demo runs

```powershell
python main.py --plain --demo bms --provider ollama
python main.py --plain --demo bms --provider gemini
```

### Requirement-specific runs

```powershell
python main.py --plain --requirement input/requirements/bms_diagnostic_java.yaml --provider ollama
python main.py --plain --requirement input/requirements/bms_diagnostic_kotlin.yaml --provider ollama
python main.py --plain --requirement input/requirements/bms_diagnostic_with_ml.yaml --provider ollama
```

### SOME/IP generator

```powershell
python src/codegen/protocol_adapter.py --requirement input/requirements/bms_diagnostic.yaml --output output/someip_service.json
```

Protocol abstraction artifacts:

```powershell
python src/codegen/protocol_adapter.py --requirement input/requirements/bms_diagnostic.yaml --output output/someip_service.json --abstraction-dir output/someip_abstraction
```

### ML train + ONNX export

```powershell
python src/ml/train.py --csv input/vehicle_data.csv --output models/tire_failure_bar.onnx
```

### Strict compliance proof

```powershell
python scripts/verify_strict_cpp_compliance.py
```

Evidence:
- `output/strict_cpp_compliance_report.json`

### Torture test evidence

```powershell
python scripts/torture_test.py --provider ollama --runs 20 --output evidence/torture_log.json
```

Quick sanity run:

```powershell
python scripts/torture_test.py --provider ollama --runs 5 --output evidence/torture_log_5.json
```

### Benchmark script

```powershell
python scripts/benchmark.py --dry-run
python scripts/benchmark.py --runs 20 --providers gemini,ollama --output benchmark_results.json
```

### Scaffolding impact metrics

```powershell
python scripts/scaffolding_impact.py --auto-services
python scripts/scaffolding_impact.py --auto-services --manual-baseline-loc 1000
```

### OTA delta evidence (v1.0 -> v1.1)

```powershell
python scripts/generate_ota_delta.py --service BMSDiagnosticService --base-version 1.0.0 --target-version 1.1.0 --base-image autoforge/bms:1.0.0 --target-image autoforge/bms:1.1.0 --base-file output/ota_v1_0.txt --target-file output/ota_v1_1.txt --output-dir output/ota_delta/BMSDiagnosticService_v1.0.0_to_v1.1.0
```

Outputs:
- `delta_manifest.json`
- `delta_chunks.json`
- `verification.json`

## CARLA integration modes

### Replay mode (current default path)

```powershell
python integrations/carla_bridge/carla_integration.py --mode replay --replay-input output/replay_seed.json --service-url http://localhost:30509 --log-path output/carla_replay_validation.json
```

### Live mode (when CARLA runtime is stable)

```powershell
python integrations/carla_bridge/carla_integration.py --mode live --host localhost --port 2000 --service-url http://localhost:30509 --log-path output/carla_live_validation.json
```

## Evidence artifacts to keep

- `output/*/audit_report.json`
- `output/*/trace.yaml`
- `output/*/traceability_matrix.csv`
- `output/*/ota_manifest.yaml`
- `output/*/variants/*.yaml`
- `output/someip_service.json`
- `models/tire_failure.onnx`
- `output/BMSDiagnosticServiceML/onnx_wrapper.hpp`
- `output/strict_cpp_compliance_report.json`
- `evidence/torture_log.json`
- `benchmark_results.json`

## Repository layout

```text
AUTOFORGE/
  config/
  input/requirements/
  integrations/
    carla_bridge/
    service_stub/
  scripts/
  src/
    llm/
    pipeline/
    codegen/
    ml/
  output/
  models/
  evidence/
  main.py
```

## Competition reporting notes

- Label replay results as replay, not live CARLA.
- Label public-dataset ML as fallback when live telemetry is unavailable.
- Keep claim -> command -> artifact mapping explicit.
- Avoid unverified absolute claims.

## License

Prepared for TELIPORT Season 3 submission context.
