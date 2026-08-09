# AUTOFORGE Design Record

> Retrospective design record for the repository implementation and generated artifacts. This document describes what the checked-in system does; it is not a certification claim.

## Problem statement

AUTOFORGE accepts a requirement YAML file and produces a service implementation plus reviewable evidence. The design targets a recurring problem in LLM-assisted automotive software work: a model can generate plausible code without demonstrating that the code satisfies the requested behavior, compiles in the target environment, or has a traceable validation record.

The repository addresses that problem with a test-first generation loop, a separate implementation role, a configurable validation gate, and a packaging phase that records traceability and supporting integration artifacts.

The primary input is a requirement under `input/requirements/`. A requirement normally names the service, language, protocol, interface, business rules, and traceability identifiers. The main C++ example is `input/requirements/bms_diagnostic.yaml`.

## Two-stage pipeline

The central design is a two-stage generation contract:

1. **Auditor stage:** the Auditor receives the requirement and generates tests before implementation code exists. The role prompt asks for boundary cases, business-rule checks, and failure-mode coverage. The generated test text is saved as `tests.py` in the service output directory.
2. **Architect stage:** the Architect receives the requirement and Auditor test text and generates the requested implementation language. The result is passed to the validation gate. A failed validation result is added as comments to the test context and the Architect is retried, up to the configured retry count.

The orchestrator wraps those stages in five operational phases:

`PARSE -> TEST_GENERATION -> CODE_GENERATION -> VALIDATION -> PACKAGING`

The default `max_retries` is three attempts. A successful validation causes packaging; otherwise the pipeline returns a rejected result and does not complete the packaging phase. The two LLM roles may use the same provider or separate providers through `--auditor-provider` and `--architect-provider`.

## Auditor and Architect responsibilities

The Auditor is a test author, not an independent proof engine. Its output is model-generated test code, and its actual authority comes from whatever language-specific checks the validation gate executes later.

The Architect is an implementation generator. It is given the Auditor output and the requested language/protocol metadata. It does not itself establish that the generated implementation is safe, standards-conformant, or deployable; those questions remain bounded by the configured gate and the evidence it emits.

The repository also provides a `mock` LLM client for deterministic local pipeline demonstrations. Mock output is useful for exercising orchestration and packaging, but it is not evidence about a remote model's generation quality.

## Validation gate

`src/pipeline/validation_gate.py` dispatches by language and returns a structured result containing validity, issues, test results, static-analysis details, and (for C++) named MISRA/ASIL-D result fields.

| Language | Implemented checks | Important boundary |
| --- | --- | --- |
| Python | Syntax compilation, configurable non-empty line-count target, optional Pylint error scan, Pytest execution | Missing Pylint is recorded as skipped; missing Pytest is a validation error |
| C++ | `-std=c++17 -fsyntax-only`, configurable line-count target, configured clang-tidy invocation, cppcheck, token-based safety heuristics, optional clang static analyzer | Default development mode can continue after compiler failure; `test_code` is not executed by the C++ validator |
| Java | Non-empty line-count target and `javac` when available | Missing `javac` is recorded as skipped |
| Kotlin | Non-empty line-count target | Kotlin compiler validation is explicitly skipped unless separately configured |
| Rust | Non-empty line-count target and `rustc --emit=metadata` when available | Missing `rustc` is recorded as skipped |

The gate is controlled by `AUTOFORGE_STRICT_VALIDATION`. With the default value `0`, some checks are advisory:

- C++ compilation failure is recorded as `WARN (dev mode - continuing despite compiler failure)`.
- A clang-tidy warning is recorded, but only parsed diagnostics containing `error` are added as gate-blocking issues.
- cppcheck can be recorded as `FAIL` without changing the top-level `valid` flag.
- ASIL-style heuristic issues become `WARN` unless strict mode is enabled.

With strict mode enabled, the C++ compiler failure, configured minimum-size failure, and ASIL heuristic failure can reject the result. Tool availability and standard-library/header availability still affect what can be proven. The resulting record is a static-analysis and quality-gate report, not a declaration of MISRA conformance, ASPICE conformance, ISO 26262 compliance, or production readiness.

## CARLA integration

`integrations/carla_bridge/carla_integration.py` supports two modes:

- **Live mode:** imports the CARLA Python package, connects to the CARLA server at the configured host/port, spawns an autopilot Tesla Model 3, reads vehicle velocity/control, and streams a selected signal set to the service endpoint.
- **Replay mode:** reads a JSON list or `{"records": [...]}` file and sends the stored signals through the same service client and logger path.

The bridge defaults to REST through `integrations/transport/rest_transport.py`. The local `integrations/service_stub/rest_bms_service.py` implements the deterministic `POST /bms/diagnostics` path plus `/health` and `/bms/latest` endpoints. The bridge records selected signals, service responses, and request latency in a JSON validation log.

The live bridge currently uses simulated battery state, battery temperature, range, and fixed tire-pressure values derived from the vehicle/control state rather than a complete physical vehicle model. Replay is therefore a service-integration path, not a substitute for a live simulator run.

The SOME/IP path is a protocol abstraction. `SomeIpTransport` returns a clear runtime-not-bound response in Python, while the protocol generator emits SOME/IP configuration and C++ skeleton artifacts. Those generated artifacts are an integration boundary, not a demonstrated deployed SOME/IP service.

## ML failure-score path

The ML path is an optional requirement extension. `src/ml/train.py`:

- loads seven-column CSV data when the required columns exist;
- otherwise generates deterministic synthetic data using seed `42`;
- uses six numeric input features: four tire pressures, vehicle speed, and ambient temperature;
- trains `sklearn.ensemble.RandomForestRegressor` with a fixed split seed, 100 trees, depth 8, and a continuous `failure_score` target;
- reports mean squared error to stdout; and
- exports the model with `skl2onnx` using a six-feature float tensor input.

The implementation is a **regressor**. A score threshold is applied only by downstream consumers: `scripts/ml_infer_carla.py` uses `0.2` for its degraded-subset summary, while the REST service stub uses `0.5` for its warning rule. These thresholds are operational choices, not calibrated clinical or safety probabilities.

`scripts/carla_log_to_csv.py` can derive a training label from logged signals using a rule-based proxy. `scripts/prepare_public_vehicle_data.py` maps public OBD telemetry to the expected schema and explicitly engineers tire-pressure and failure-score proxies. Neither path supplies ground-truth tire-failure outcomes.

## ONNX export boundary

There are two separate ONNX concerns:

1. **Python model artifact:** training and export are performed in Python. Inference is performed by `scripts/ml_infer_carla.py` through `onnxruntime` with `CPUExecutionProvider`.
2. **C++ wrapper artifact:** a requirement with an `ml` block causes the packaging phase to request an ONNX Runtime wrapper from `ONNXWrapperGenerator`. If that LLM call fails, the orchestrator writes a fallback wrapper that reports a zero score and contains a TODO for binding an ONNX Runtime session.

The wrapper is packaged alongside generated service code; the repository does not demonstrate a complete build, link, and runtime call from the generated SOME/IP service into ONNX Runtime. Existing wrapper text also needs normal compiler/integration checks before it can be treated as build-ready C++.

## Design trade-offs

- **Adversarial roles vs. operational simplicity:** separate prompts and providers make the generation contract inspectable, but generation remains dependent on model availability and output quality.
- **Retry loop vs. reproducibility:** feeding validation issues back into a fresh generation attempt can recover from transient or correctable failures, while remote/local model responses remain variable.
- **Optional tools vs. portability:** skipping unavailable compilers and analyzers keeps the pipeline runnable across developer machines, but a skipped check is not equivalent to a pass.
- **REST validation vs. SOME/IP artifacts:** REST and the local stub make service behavior easy to exercise; generated SOME/IP assets preserve a middleware mapping without pretending that runtime binding is already complete.
- **Fallback data vs. data fidelity:** deterministic synthetic/public-mapped data keeps the ML path runnable, but it weakens claims about real vehicle failure prediction.
- **Structured artifacts vs. artifact governance:** JSON/YAML/CSV outputs are easy to inspect and diff, but they currently lack a single run manifest that binds every model, dataset, source revision, tool version, and output hash together.

## Non-goals

AUTOFORGE is not, by itself:

- a guarantee of MISRA conformance or ASPICE process compliance;
- a safety case, safety certification, or ISO 26262 assessment;
- a production ECU, vehicle-bus, SOME/IP middleware, HIL, or hardware deployment;
- a replacement for compiler/header/toolchain configuration in the target build environment;
- a calibrated classifier, failure-probability estimator, or validated diagnostic model;
- evidence that generated code is production-ready solely because a pipeline result is `ACCEPTED`; or
- a complete lifecycle system for change control, independent review, requirements baselining, or release approval.
