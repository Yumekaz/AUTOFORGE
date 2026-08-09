# AUTOFORGE

> Test-first GenAI workflow for automotive service code generation.

AUTOFORGE turns requirement YAML into generated service code, tests, validation results, and reviewable engineering artifacts. Its core idea is simple: have one model role write the tests first, have a separate role implement against those tests, then run configurable static-analysis and quality gates before packaging the result.

This repository is a development and research prototype. It demonstrates the workflow, integrations, and evidence artifacts described below. It does not claim guaranteed MISRA conformance, ASPICE compliance, safety certification, production readiness, or deployable vehicle middleware.

## What it does

- Parses service requirements from YAML.
- Uses separate Auditor and Architect roles for test-first generation.
- Retries implementation after validation feedback, up to the configured limit.
- Runs language-specific compile, test, static-analysis, and heuristic checks when the relevant tools are available.
- Packages generated code, tests, traceability matrices, protocol artifacts, OTA metadata, and audit reports.
- Connects a service endpoint to CARLA in live mode or to recorded signals in replay mode.
- Trains a six-feature `RandomForestRegressor` and exports an ONNX model that produces a continuous failure score.

## How the pipeline works

```text
Requirement YAML
      |
      v
Parse -> Auditor generates tests -> Architect generates code
                                      |
                                      v
                         Validation and quality gates
                          | pass              | fail
                          v                   v
                       Package          Feed issues into retry
```

The implementation is organized as five phases:

`PARSE -> TEST_GENERATION -> CODE_GENERATION -> VALIDATION -> PACKAGING`

The Auditor and Architect can use the same provider or separate providers. A deterministic mock provider is available for a local orchestration smoke test without an LLM API.

## Quickstart

Use an existing Python environment with the dependencies already installed:

```powershell
python main.py --plain --demo bms --mock
```

This exercises the pipeline with mock generation and writes artifacts under `output/BMSDiagnosticService/`.

For a normal local setup, see [`COMMANDS.md`](COMMANDS.md). The dependency file covers the Python pipeline and ML export path; live CARLA, ONNX Runtime, C++ compilers/headers, clang-tidy, cppcheck, Java, Kotlin, and SOME/IP middleware are separate optional prerequisites.

## Run the main paths

### Requirement-to-artifact generation

```powershell
python main.py --plain --requirement input\requirements\bms_diagnostic.yaml --provider ollama
```

Mixed-provider generation is also supported:

```powershell
python main.py --plain --demo bms --provider ollama --auditor-provider gemini --architect-provider ollama
```

### Fallback orchestration

```powershell
python scripts\run_fallback_mode.py
```

This path trains the model, generates protocol artifacts, runs requirement variants, starts the local REST stub, replays recorded signals, and checks expected outputs. It still requires the selected LLM provider and the source data expected by `scripts\prepare_public_vehicle_data.py`; replay mode itself does not require a live CARLA server.

### CARLA live mode

```powershell
python scripts\run_live_mode.py --provider ollama --skip-gemini --with-hmi-dashboard --max-samples 200 --rate-hz 10
```

Live mode requires a running CARLA server and a compatible CARLA Python environment. The bridge defaults to REST transport. Replay mode uses the same service client and logger with a JSON input:

```powershell
python integrations\carla_bridge\carla_integration.py --mode replay --replay-input output\replay_seed.json --service-url http://localhost:30509 --log-path output\carla_replay_validation.json
```

The generated SOME/IP files are protocol-abstraction artifacts. The Python SOME/IP transport is intentionally not a bound runtime transport; local validation uses REST.

### ML training and ONNX inference

The training implementation is a regression path, not a classifier. It consumes four tire-pressure features, vehicle speed, and ambient temperature, then predicts a continuous `failure_score`.

```powershell
python src\ml\train.py --csv input\vehicle_data.csv --output models\tire_failure_bar.onnx
python scripts\ml_infer_carla.py --model models\tire_failure_bar.onnx --csv input\vehicle_data_carla.csv --out-csv output\ml\carla_inference_bar_predictions.csv --out-json output\ml\carla_inference_bar_summary.json
```

The repository's public-data and CARLA conversion paths use engineered proxy labels. The resulting scores are not calibrated probabilities or measured failure outcomes.

### Validation and evidence scripts

```powershell
python scripts\verify_strict_cpp_compliance.py
python scripts\torture_test.py --provider ollama --runs 20 --output evidence\torture_log.json
python scripts\benchmark.py --dry-run
```

The strict C++ script is a toolchain-readiness check over a reference snippet. Its report must be read field by field because analyzer/header availability is recorded separately from the top-level result.

## Evidence snapshot

These are repository-recorded results, not guarantees about future runs:

| Area | Recorded result | Evidence |
| --- | --- | --- |
| 50-run pipeline record | 39 accepted, 11 failed, 78.0% acceptance; failures are recorded as test-generation timeouts | [`evidence/torture_log_real_50.json`](evidence/torture_log_real_50.json) |
| Gemini benchmark | 5/5 pipeline successes, 39.2 s average latency; compilation and ASIL fields both 0% | [`benchmark_results_real.json`](benchmark_results_real.json) |
| CARLA live record | 200 samples, 2,052.43 ms average latency, no recorded warnings | [`output/carla_live_validation.json`](output/carla_live_validation.json) |
| CARLA replay | 2 samples; the low-SOC/high-temperature seed produces warnings | [`output/carla_replay_validation.json`](output/carla_replay_validation.json) |
| ML baseline/stress scores | Mean scores 0.106793 and 0.210848 over 200 rows each using `tire_failure_bar.onnx` | [`output/ml/carla_inference_bar_summary.json`](output/ml/carla_inference_bar_summary.json), [`output/ml/carla_inference_bar_stress_summary.json`](output/ml/carla_inference_bar_stress_summary.json) |

The full evidence interpretation, model/data hashes, reproduction status, and known artifact inconsistencies are documented in [`docs/EVALUATION.md`](docs/EVALUATION.md).

## Capability boundaries

### Implemented in the repository

- Requirement parsing and multi-language code-generation templates.
- Auditor-first test generation and Architect implementation generation.
- Configurable validation gate with compiler, Pytest/Pylint, clang-tidy, cppcheck, Java, Rust, Kotlin, and heuristic paths.
- Traceability matrices, phase audit reports, OTA manifests, variants, and protocol configuration generation.
- REST service stub and CARLA live/replay bridge.
- Random-forest regression training, ONNX export, and CPU inference script.

### Not established by the repository

- Full MISRA rule coverage, ASPICE process compliance, ISO 26262/ASIL compliance, or safety certification.
- A production ECU, complete SOME/IP wire deployment, HIL setup, or target-platform build.
- A calibrated tire-failure classifier or validated field-performance model.
- Independent verification of every generated artifact merely because a pipeline result is `ACCEPTED`.

Unavailable tools can be recorded as `SKIP`, and default C++ development mode can continue after compiler warnings or failures. Read [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) before interpreting a gate result.

## Repository layout

| Path | Purpose |
| --- | --- |
| `input/requirements/` | Example service requirements |
| `src/pipeline/` | Orchestration, validation, traceability, reporting, and ONNX wrapper generation |
| `src/codegen/` | Service and protocol artifact generation |
| `src/ml/` | Regression training and ONNX export |
| `integrations/carla_bridge/` | Live/replay CARLA bridge and validation logger |
| `integrations/service_stub/` | Deterministic local REST service |
| `scripts/` | Demo, benchmark, data, inference, and evidence commands |
| `models/` | Checked-in ONNX artifacts |
| `output/` | Generated services and reports |
| `evidence/` | Torture-test records |
| `docs/` | Design, evaluation, and limitations records |

## Documentation

- [`docs/DESIGN.md`](docs/DESIGN.md) — retrospective architecture, pipeline responsibilities, validation gates, CARLA, ML, ONNX boundaries, trade-offs, and non-goals.
- [`docs/EVALUATION.md`](docs/EVALUATION.md) — recorded runs, CARLA and health-signal evidence, model/data identity, generated artifacts, commands, and what was reproduced.
- [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) — optional tools, compiler/header behavior, fallback paths, static-analysis limits, dataset/model limits, and simulation boundaries.
- [`COMMANDS.md`](COMMANDS.md) — extended setup and execution commands.
- [`PROTOCOL_ABSTRACTION_SOMEIP.md`](PROTOCOL_ABSTRACTION_SOMEIP.md) — SOME/IP abstraction scope.
