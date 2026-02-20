# AUTOFORGE

## AUTOFORGE
AUTOFORGE is a test-first, adversarial GenAI system for automotive SDV backend generation. It converts requirement YAML files into implementation code plus audit-grade artifacts (traceability, OTA, protocol mapping, validation logs). The key difference from raw GenAI code generation is control: two role-separated agents, deterministic validation gates, and reproducible evidence outputs instead of one-shot unverifiable code.

## The Core Innovation
- **Adversarial agents:** the Auditor writes strict tests and constraints first; the Architect must satisfy those constraints.
- **Validation gate:** compile/static/test/ASIL-style checks enforce quality before packaging; failed runs are retried with concrete error feedback.
- **Evidence artifacts:** each run emits traceability, audit, protocol, OTA, and optional ML integration artifacts for competition-grade proof.

## Quick Demo (3 steps)
1. `git clone https://github.com/Yumekaz/AUTOFORGE`
2. `pip install -r requirements.txt`
3. `python scripts/run_fallback_mode.py`

## What Gets Generated
| Input YAML | Output artifacts |
|---|---|
| `input/requirements/*.yaml` | Generated service code (`.cpp` / `.java` / `.kt`), `someip_service.json`, `ota_manifest.yaml` + variant configs, traceability matrix (`.csv`/`.yaml`), optional ONNX wrapper (`onnx_wrapper.hpp`) |

## Evidence Summary
- **Torture test:** 50 runs, 78% pass rate ([`evidence/torture_log_real_50.json`](evidence/torture_log_real_50.json))
- **Benchmark:** Gemini average 39.2s generation latency, 100% success ([`benchmark_results_real.json`](benchmark_results_real.json))
- **ML signal separation:** Healthy 0.107 vs Degraded 0.626 failure score ([`output/ml/`](output/ml/))
- **CARLA validation:** 200-sample replay validation ([`output/carla_live_validation.json`](output/carla_live_validation.json))

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





