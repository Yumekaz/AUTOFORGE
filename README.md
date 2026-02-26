# AUTOFORGE

AUTOFORGE is an adversarial, test-first GenAI pipeline for automotive SDV service generation. It converts requirement YAML into implementation code and evidence artifacts with deterministic validation gates. The practical difference from raw one-shot GenAI is governance: separate Auditor/Architect roles, hard validation before acceptance, and traceable outputs for review.

## The Core Innovation
- **Adversarial agents:** Auditor generates strict tests first; Architect must satisfy them.
- **Validation gate:** compile/static/test/ASIL-style checks decide accept/reject and drive retry.
- **Evidence-first packaging:** each run emits audit, traceability, protocol, OTA, and optional ML wrapper artifacts.

## Quick Demo (3 steps)
1. `git clone https://github.com/Yumekaz/AUTOFORGE`
2. `pip install -r requirements.txt`
3. `python scripts/run_fallback_mode.py`

Live demo command (CARLA + HMI):
- `python scripts/run_live_mode.py --provider ollama --skip-gemini --with-hmi-dashboard --max-samples 200 --rate-hz 10`

## What Gets Generated
| Input YAML | Output artifacts |
|---|---|
| `input/requirements/*.yaml` | Service code (`.cpp` / `.java` / `.kt`), `someip_service.json`, `ota_manifest.yaml` + variants, traceability matrix (`.csv`/`.yaml`), optional `onnx_wrapper.hpp` |

## Evidence Summary
- **Torture test:** 50 runs, 78% pass rate ([`evidence/torture_log_real_50.json`](evidence/torture_log_real_50.json))
- **Benchmark:** Gemini average 39.2s generation latency, 100% success ([`benchmark_results_real.json`](benchmark_results_real.json))
- **ML separation:** Healthy 0.107 vs Degraded 0.626 failure score ([`output/ml/carla_inference_bar_stress_summary.json`](output/ml/carla_inference_bar_stress_summary.json))
- **CARLA validation:** 200-sample live validation log ([`output/carla_live_validation.json`](output/carla_live_validation.json))

## Evidence Index (Judge Quick-View)
### Reliability + Performance
- [`evidence/torture_log_real_50.json`](evidence/torture_log_real_50.json)
- [`benchmark_results_real.json`](benchmark_results_real.json)

### CARLA + HMI
- [`output/carla_live_validation.json`](output/carla_live_validation.json)
- [`integrations/carla_bridge/carla_integration.py`](integrations/carla_bridge/carla_integration.py)
- [`scripts/live_hmi_dashboard.py`](scripts/live_hmi_dashboard.py)

### ML + ONNX
- [`models/tire_failure.onnx`](models/tire_failure.onnx)
- [`output/ml/carla_inference_bar_stress_summary.json`](output/ml/carla_inference_bar_stress_summary.json)
- [`output/ml/carla_failure_score_distribution_bar_stress.png`](output/ml/carla_failure_score_distribution_bar_stress.png)

### SOME/IP Protocol Abstraction
- [`output/BMSDiagnosticService/someip_service.json`](output/BMSDiagnosticService/someip_service.json)
- [`output/BMSDiagnosticService/protocol_abstraction/vsomeip_config.json`](output/BMSDiagnosticService/protocol_abstraction/vsomeip_config.json)
- [`output/BMSDiagnosticService/protocol_abstraction/protocol_mapping.md`](output/BMSDiagnosticService/protocol_abstraction/protocol_mapping.md)
- [`PROTOCOL_ABSTRACTION_SOMEIP.md`](PROTOCOL_ABSTRACTION_SOMEIP.md)

### OTA + Variants + Traceability
- [`output/ota_delta/BMSDiagnosticService_v1.0.0_to_v1.1.0/delta_manifest.json`](output/ota_delta/BMSDiagnosticService_v1.0.0_to_v1.1.0/delta_manifest.json)
- [`output/ota_delta/BMSDiagnosticService_v1.0.0_to_v1.1.0/verification.json`](output/ota_delta/BMSDiagnosticService_v1.0.0_to_v1.1.0/verification.json)
- [`output/BMSDiagnosticService/ota_manifest.yaml`](output/BMSDiagnosticService/ota_manifest.yaml)
- [`output/BMSDiagnosticService/variants/config_ev.yaml`](output/BMSDiagnosticService/variants/config_ev.yaml)
- [`output/BMSDiagnosticService/variants/config_hybrid.yaml`](output/BMSDiagnosticService/variants/config_hybrid.yaml)
- [`output/BMSDiagnosticService/variants/config_ice.yaml`](output/BMSDiagnosticService/variants/config_ice.yaml)
- [`output/BMSDiagnosticService/traceability_matrix.csv`](output/BMSDiagnosticService/traceability_matrix.csv)
- [`output/BMSDiagnosticService/audit_report.json`](output/BMSDiagnosticService/audit_report.json)

## Reproduce Key Runs
- **Fallback full run:** `python scripts/run_fallback_mode.py`
- **Live run (CARLA required):** `python scripts/run_live_mode.py --provider ollama --skip-gemini --with-hmi-dashboard --max-samples 200 --rate-hz 10`
- **Mixed-agent run (Auditor=Gemini, Architect=Ollama):** `python main.py --plain --demo bms --provider ollama --auditor-provider gemini --architect-provider ollama`
- **Note:** `--skip-gemini` skips only the extra standalone Gemini demo step inside `run_live_mode.py`. It does not disable split-agent runs from `main.py`.

## Case Study 2 Coverage
| Case Study requirement | Status |
|---|---|
| Requirements -> design/code/tests | Implemented |
| SOME/IP protocol support | Implemented |
| OTA + variant configs (ICE/Hybrid/EV) | Implemented |
| Multi-language (C++, Java, Kotlin) | Implemented |
| Predictive analytics (supervised ML + ONNX) | Implemented |
| MISRA/ASPICE-style evidence | Implemented |
| CARLA simulation validation | Live mode implemented (replay as fallback) |
| LLM benchmarking | Implemented |

## Full Documentation
All setup, pipeline, integration, validation, and benchmark commands are documented in [`COMMANDS.md`](COMMANDS.md).



