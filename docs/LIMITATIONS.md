# AUTOFORGE Limitations Record

> Retrospective limitations record for the repository implementation. The limitations below are part of the system boundary and should be read alongside the generated reports.

## Optional tool behavior

AUTOFORGE resolves several tools from `PATH` and a small set of Windows locations. Availability changes the meaning of a report:

| Tool/path | If available | If unavailable or incomplete |
| --- | --- | --- |
| C++ compiler | Runs a C++17 syntax-only check | Records a skip or, in development mode, a warning; it does not establish buildability |
| `clang-tidy` | Runs the configured check set from `config/misra/clang-tidy-misra.yaml` | Records a skip; the pipeline can still accept in default mode |
| `cppcheck` | Runs `--enable=all` with selected suppressions | Records a skip; a reported cppcheck failure is not independently wired to the top-level C++ validity flag |
| `clang --analyze` | Adds static-analyzer output to the ASIL-style result | Skips when clang or standard headers are missing; missing headers are not a clean analyzer pass |
| `pylint` | Scans Python for enabled error/fatal categories | Records a skip when absent |
| `pytest` | Executes generated Python tests | Missing Pytest is a validation error for Python |
| `javac` | Performs a Java compilation check | Records a skip when absent |
| `kotlinc` | Not currently wired into the gate | Kotlin is reported as a lightweight, compiler-skipped path |
| `rustc` | Runs metadata compilation | Records a skip when absent |
| `onnxruntime` | Runs CPU ONNX inference | The inference script stops with a dependency error |
| CARLA package/server | Runs live bridge mode | Replay or local REST fallback is required |

A `PASS` for one available tool does not imply that skipped or advisory tools passed.

## Missing compiler and header behavior

The C++ gate prefers `clang++`, then falls back to a resolved `g++`, and supports `AUTOFORGE_CXX` as an override. It compiles generated source with `-std=c++17 -fsyntax-only`.

In the stored BMS reports, the environment could not find standard headers such as `cstdint`; the ML report also records a missing `someip/someip.hpp`. In default mode, these become `WARN (dev mode - continuing despite compiler failure)`, allowing the pipeline to package artifacts. The strict proof report records a top-level pass while its clang static analyzer status is `SKIP (clang stdlib headers unavailable)`, which is why the report must be read field by field.

The repository does not provide the target compiler, standard library, SOME/IP SDK, include paths, linker configuration, or generated build system needed to turn source artifacts into a target binary.

## Fallback generation

Fallbacks are deliberate availability paths, not equivalent validations:

- `src/ml/train.py` creates deterministic synthetic data when no CSV path is provided or the path does not exist.
- `scripts/prepare_public_vehicle_data.py` creates a mapped public-data CSV using engineered tire-pressure and failure-score proxies.
- `scripts/run_fallback_mode.py` uses a deterministic replay seed and a local REST service stub when live CARLA is unavailable.
- The orchestrator writes a fallback ONNX wrapper after a wrapper-generation exception. That wrapper returns `0.0f` from `predict_failure_score` and contains a TODO for the ONNX Runtime session binding.
- The mock LLM client returns hard-coded demonstration responses.

Fallback success proves that the fallback path can produce or process artifacts. It does not prove live-model quality, physical realism, toolchain compatibility, or middleware behavior.

## Static-analysis and quality-gate limitations

The repository implements static-analysis and quality gates, but the checks are deliberately bounded:

- The clang-tidy configuration enables broad `cppcoreguidelines`, `bugprone`, `readability`, `misc`, `performance`, and `modernize` families. It is not a complete implementation of every MISRA rule, and the source labels are not evidence of licensed rule coverage.
- clang-tidy output is parsed for lines containing `warning:` or `error:`. Only parsed text containing `error` is added as a blocking issue.
- cppcheck failure is recorded in `static_analysis`, but the C++ validator does not set `valid = False` solely from cppcheck's nonzero exit code.
- C++ validation does not execute the generated `test_code`; its `test_results` object remains empty. Python has the explicit Pytest execution path.
- The ASIL-style validator uses token presence for unsafe APIs, nondeterminism, unbounded loops, defensive signals, and bounds signals. These heuristics can miss semantic defects and can also be affected by harmless text matches.
- The optional clang analyzer runs on a temporary source file and can skip because of missing system headers.
- Java validation is compile-only when `javac` exists. Kotlin validation is a size check plus an explicit compiler skip. There is no equivalent cross-language test execution gate.
- The CI workflow installs dependencies on a GitHub runner and uses `|| true` for its unit-test and formatting checks. A local report or CI job should therefore be interpreted by its individual command results rather than by the existence of a green-looking workflow step.

These checks are useful review signals. They are not a safety case, independent verification, or certification package.

## Dataset and model limitations

- The model source uses `RandomForestRegressor`; it predicts a continuous score and is not a classifier.
- `failure_score` is a proxy label in the public-data and CARLA conversion paths. The public source has no direct tire-pressure or failure labels, and the CARLA converter derives labels from hand-written rules.
- The checked-in healthy and stress CARLA CSVs have identical `failure_score` columns despite changes in selected features. This prevents treating the pair as ground-truth classification data.
- Training prints a test-set MSE but no checked-in training report binds that MSE to a dataset hash, model hash, preprocessing version, library versions, or split manifest.
- The inference script applies a `0.2` degraded-subset threshold, while the REST stub applies a `0.5` warning threshold. The thresholds are not shown as calibrated or optimized.
- The repository contains multiple ONNX artifacts, but no single model manifest explains their provenance. Two compatibility paths are byte-identical while `tire_failure_carla.onnx` is different.
- The current ML output filenames are reused by multiple commands. A summary can point to a path whose CSV was later overwritten by another run.
- This repository does not include a model card, uncertainty estimate, drift monitor, external validation cohort, or measured field-outcome evaluation.

## CARLA and simulation boundaries

Live mode connects the bridge to CARLA, but several signals are simulated or fixed in the bridge. The local REST service stub evaluates business rules in a Python process. Replay uses a small JSON seed. These paths exercise signal transport, response logging, and selected warning logic; they do not represent an ECU, a real vehicle network, a plant model validated against measurements, or hardware-in-the-loop behavior.

The generated SOME/IP artifacts are intentionally described as protocol abstraction. The Python SOME/IP transport returns a runtime-not-bound response, and generated C++ handlers contain integration placeholders such as payload serialization TODOs. No end-to-end SOME/IP wire exchange is demonstrated by the repository-recorded CARLA logs.

## Production and assurance boundary

The project does not establish guaranteed MISRA conformance, ASPICE compliance, ISO 26262/ASIL compliance, safety certification, cybersecurity approval, release approval, or production readiness. It does not replace requirements baselining, independent review, configuration management, target-platform testing, timing analysis, resource analysis, fault injection, safety-case work, or operational monitoring.

The appropriate public claim is that AUTOFORGE provides a test-first code-generation workflow with static-analysis and quality gates, optional CARLA/replay integration, regression-model/ONNX artifacts, and structured reports whose strength depends on tool availability and data provenance.
