# AUTOFORGE Evaluation Record

> Retrospective evaluation record based on repository-recorded outputs and read-only reproduction of selected summaries. It reports evidence and boundaries; it does not convert the artifacts into compliance or certification claims.

## Evaluation basis

The repository state examined contains the implementation, generated outputs, datasets, ONNX files, reports, scripts, and README. The project pipelines were not rerun during this documentation pass, and no dependencies were installed. The values marked **reproduced** below were recalculated from checked-in JSON/CSV files with read-only inspection; the values marked **recorded** are taken from the committed report that produced them.

## Existing 50-run results

`evidence/torture_log_real_50.json` records an Ollama run dated `2026-02-19T01:07:59.926378+05:30` with seed `42` across four requirements:

| Measure | Recorded value |
| --- | ---: |
| Runs | 50 |
| Accepted runs | 39 |
| Failed runs | 11 |
| Acceptance rate | 78.0% |
| Average duration | 227.757 s |
| Average retries | 0.84 |
| Total wall time | 11,387.851 s |

The 11 failed records all contain `Test generation error: timed out`. The per-requirement split in the same file is:

| Requirement | Runs | Accepted | Rate |
| --- | ---: | ---: | ---: |
| `bms_diagnostic.yaml` | 13 | 10 | 76.92% |
| `tire_pressure_diagnostic.yaml` | 13 | 9 | 69.23% |
| `motor_health_diagnostic.yaml` | 12 | 10 | 83.33% |
| `bms_diagnostic_with_ml.yaml` | 12 | 10 | 83.33% |

`evidence/torture_log_target_profile.json` is a separate target-profile record. It reports 41 detection runs out of 50 (82.0%), 115 total retries, 2.3 average retries, zero unsafe-code escapes, and a maximum observed retry count of 3 against a configured limit of 3. It should not be merged with the 39/50 acceptance result because it uses a different result schema and purpose.

## Benchmark record

`benchmark_results_real.json` records five non-dry-run Gemini executions of the C++ BMS requirement:

| Measure | Recorded value |
| --- | ---: |
| Pipeline success rate | 100% (5/5) |
| Average latency | 39,200 ms |
| Average retries | 1.0 |
| clang-tidy field | 100% pass |
| Compilation field | 0% pass |
| ASIL-D field | 0% pass |

The benchmark's `success` field reflects the pipeline result, while the compilation and ASIL fields are collected from an additional validation call. The repository therefore records successful pipeline packaging in an environment where compilation was not passing. The report itself does not prove that the generated C++ was buildable.

`benchmark_results.json` is another five-run Gemini record with 0% success and 1,028.8 ms average latency. It is retained as a separate artifact and should not be silently replaced by the later `benchmark_results_real.json` result.

## CARLA sample evidence

### Live record

`output/carla_live_validation.json` records 200 samples. Its stored summary reports an average request latency of 2,052.43 ms and p95 latency of 2,072.31 ms. A read-only pass over the records reproduced:

- 200 records with `health_status = 0`;
- zero records containing warnings;
- battery temperature from 25°C to approximately 42°C;
- battery SOC from 20% to approximately 20.366%; and
- the selected tire-pressure values fixed at 2.5/2.5/2.4/2.4 in the logged records.

The file is a repository-recorded live-mode artifact. This documentation pass did not reconnect to CARLA or independently reproduce the run.

### Replay record

`output/carla_replay_validation.json` records the two-sample seed used by fallback mode. The first sample has SOC 18 and battery temperature 48°C, producing `health_status = 1` with low-battery and high-temperature warnings. The second sample has SOC 65 and temperature 30°C, producing `health_status = 0` with no warnings. The stored summary reports 2,060.24 ms average latency.

Replay proves the service/client/logger path against known inputs. It is not a live CARLA result.

## Health-signal results

The local REST stub evaluates low SOC, high/critical temperature, high-speed low tire pressure, and an ML score threshold. The recorded live log exercised none of those warning conditions. The recorded replay seed exercised the low-SOC and high-temperature branches once each in the same response, and the normal sample exercised the no-warning path.

The generated C++ services and the REST stub are different execution paths. A health result from the stub is evidence for that deterministic stub path, not evidence that a generated SOME/IP service has been deployed or that a vehicle ECU would behave identically.

## Model and data identity

The checked-in model and data identities are:

| Artifact | Rows/size | SHA-256 |
| --- | ---: | --- |
| `input/vehicle_data.csv` | 200,000 rows; 19,245,389 bytes | `0db2dd40565f9f005de603cf5a4ff13e1b6a6b7d963bd8ca0143636611ae41c8` |
| `input/vehicle_data_bar_synth.csv` | 200,000 rows; 26,079,185 bytes | `3e4163117808f245511b59437a4d86ec1238189eab6797bba13b13bd27fc4696` |
| `input/vehicle_data_carla.csv` | 200 rows; 10,958 bytes | `35c4a26ee3b93c285848fbf5e0a375588de3b541f3dd5a988063244ad3fe30f` |
| `input/vehicle_data_carla_stress.csv` | 200 rows; 11,401 bytes | `178bd6abcd36a3d16cd6530d5427c7cb535320f210fcdb5a5f4c8224d9806107e` |
| `models/tire_failure.onnx` | 1,961,900 bytes | `e6c7ecc447d9732a9573b7324bf81652b99df96a7dc9325c4dc27f3c7770abcf` |
| `models/tire_failure_bar.onnx` | 1,961,900 bytes | `e6c7ecc447d9732a9573b7324bf81652b99df96a7dc9325c4dc27f3c7770abcf` |
| `models/tire_failure_carla.onnx` | 464,058 bytes | `789a4e46f84ec06ddd7ee0f463d707f5c5c70ea4993baaf9c40a850e7cbfacdd2` |

The identical hashes for `tire_failure.onnx` and `tire_failure_bar.onnx` show that those two files are byte-identical compatibility paths in the current checkout. The repository does not include a model card or a single manifest tying each ONNX file to a training command, library versions, and dataset hash.

The source implements `RandomForestRegressor`, six numeric inputs, a fixed `random_state=42`, and a continuous `failure_score` target. The model is therefore described here as a regression model producing a failure score, not as a classifier.

The two CARLA CSVs each have 200 rows. Their stored `failure_score` columns are identical even though the stress file changes some pressure, speed, and temperature inputs. This means the CSV labels do not independently establish a healthy-versus-degraded ground truth. The recorded inference summaries are useful as artifact outputs, but they should not be interpreted as calibrated probabilities or classification accuracy.

## Recorded ML outputs

The `tire_failure_bar.onnx` summaries record:

| Input | Samples | Mean score | Minimum | Maximum |
| --- | ---: | ---: | ---: | ---: |
| `input/vehicle_data_carla.csv` | 200 | 0.106793 | 0.076892 | 0.120538 |
| `input/vehicle_data_carla_stress.csv` | 200 | 0.210848 | 0.076892 | 0.722213 |

Those values are repository-recorded in `output/ml/carla_inference_bar_summary.json` and `output/ml/carla_inference_bar_stress_summary.json`, and were also reproduced from the corresponding prediction CSVs. The summary files reuse output naming conventions in places: both stress and non-stress workflows can point at `output/ml/carla_inference_predictions.csv`. The current CSV contents and summaries are therefore best treated as separately recorded outputs, not as one immutable run manifest.

## Generated artifacts

The packaging phase can emit:

- generated service code and generated tests under `output/<ServiceName>/`;
- `audit_report.json`, `trace.yaml`, and CSV/YAML traceability matrices;
- protocol JSON plus SOME/IP abstraction skeletons and mapping documentation;
- OTA manifest and vehicle-variant YAML files;
- `carla_service_config.yaml`;
- optional `onnx_wrapper.hpp` and model artifacts;
- CARLA live/replay validation logs;
- ML prediction CSVs, summaries, and plots; and
- top-level benchmark, torture, strict-check, metrics, and dataset-mapping reports.

These files are evidence artifacts generated by scripts and pipeline runs. Their presence means that a report was emitted, not that every referenced external tool or runtime integration was available for that run.

## Exact commands

The following commands are the repository's documented execution paths. They require the relevant dependencies, services, model/runtime libraries, and (for live mode) CARLA to already be available.

```powershell
python scripts\run_fallback_mode.py
python scripts\run_live_mode.py --provider ollama --skip-gemini --with-hmi-dashboard --max-samples 200 --rate-hz 10
python src\ml\train.py --csv input\vehicle_data.csv --output models\tire_failure_bar.onnx
python scripts\carla_log_to_csv.py --input output\carla_live_validation.json --output input\vehicle_data_carla.csv
python scripts\ml_infer_carla.py --model models\tire_failure_bar.onnx --csv input\vehicle_data_carla.csv --out-csv output\ml\carla_inference_bar_predictions.csv --out-json output\ml\carla_inference_bar_summary.json
python scripts\ml_infer_carla.py --model models\tire_failure_bar.onnx --csv input\vehicle_data_carla_stress.csv --out-csv output\ml\carla_inference_bar_stress_predictions.csv --out-json output\ml\carla_inference_bar_stress_summary.json
python scripts\verify_strict_cpp_compliance.py
python scripts\torture_test.py --provider ollama --runs 20 --output evidence\torture_log.json
python scripts\benchmark.py --dry-run
python scripts\benchmark.py --runs 20 --providers gemini,ollama --output benchmark_results.json
python integrations\carla_bridge\carla_integration.py --mode replay --replay-input output\replay_seed.json --service-url http://localhost:30509 --log-path output\carla_replay_validation.json
python integrations\carla_bridge\carla_integration.py --mode live --host localhost --port 2000 --service-url http://localhost:30509 --log-path output\carla_live_validation.json
```

The one-command fallback and live scripts also invoke the requirement pipeline, generate a compatibility model copy, run Java/Kotlin variants, start the local REST stub, and verify a list of expected artifacts.

## Repository-recorded versus reproduced

| Statement | Status in this record |
| --- | --- |
| 39/50 result, 78% acceptance | Repository-recorded; per-requirement counts reproduced from the JSON |
| 5/5 Gemini pipeline successes with 0% compilation/ASIL fields | Repository-recorded from `benchmark_results_real.json` |
| 200 live CARLA samples and latency summary | Repository-recorded; counts and health distribution reproduced from the JSON |
| Replay warning behavior | Repository-recorded; response branches reproduced from the JSON |
| Dataset row counts, model sizes, hashes, CSV equality checks | Reproduced read-only from the checked-in files |
| ML prediction means and ranges | Repository-recorded in summaries and reproduced from prediction CSVs |
| End-to-end fallback/live rerun | Not reproduced in this documentation pass |
| ONNX graph loading with `onnx`/`onnxruntime` | Not reproduced here; those packages were not available in the inspection environment |
