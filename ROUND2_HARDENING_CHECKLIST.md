# Round 2 Hardening Checklist

Purpose: maximize Round-2 score with a defensible, reproducible software-first submission.

## 1. Pre-Run Setup (Friend's Machine)
- [ ] Python 3.10+ installed
- [ ] `pip install -r requirements.txt`
- [ ] `pip install PyPDF2` (if PDF parsing needed)
- [ ] `clang`, `clang-tidy`, `cppcheck`, `g++` installed
- [ ] `rustc` installed (for Rust validation path)
- [ ] CARLA installed/running (if using live sim)
- [ ] Optional: Ollama installed with `llama3.1:8b`
- [ ] API keys set: `GOOGLE_API_KEY`, `OPENAI_API_KEY` (if used), `GROQ_API_KEY`

## 2. Dry Validation First (No API Risk)
- [ ] Run benchmark dry mode:
  - `python scripts/benchmark.py --dry-run`
- [ ] Confirm outputs exist:
  - `benchmark_results.json`
  - `benchmark_results.md`
  - `benchmark_slide7.md`

Pass criteria:
- [ ] JSON has all providers and summaries
- [ ] Slide table renders correctly

## 3. Pipeline Evidence Run (Real)
- [ ] Run pipeline with one requirement:
  - `python main.py --requirement input/requirements/bms_diagnostic.yaml --provider gemini`
- [ ] Confirm output artifacts:
  - `output/<Service>/audit_report.json`
  - `output/<Service>/trace.yaml`
  - `output/<Service>/traceability_matrix.csv`
  - `output/<Service>/traceability_matrix.yaml`
  - `output/metrics_summary.json`

Pass criteria:
- [ ] `validation_passed: true`
- [ ] traceability matrix not empty
- [ ] audit phases are populated

## 4. CARLA Demo Path
- [ ] Start service stub:
  - `python integrations/service_stub/rest_bms_service.py`
- [ ] Run CARLA bridge:
  - `python integrations/carla_bridge/carla_integration.py --log-path output/carla_validation.json`
- [ ] Confirm output:
  - `output/carla_validation.json`

Pass criteria:
- [ ] log has non-zero samples
- [ ] latency metrics present (`avg_latency_ms`, `p95_latency_ms`)
- [ ] warnings appear for unsafe states

## 5. Multi-LLM Benchmark (Real)
- [ ] Run:
  - `python scripts/benchmark.py --runs 20 --providers gemini,ollama,groq`
- [ ] Confirm outputs:
  - `benchmark_results.json`
  - `benchmark_slide7.md`

Pass criteria:
- [ ] each provider has 20 runs
- [ ] latency/retry/misra/asil fields are populated

## 6. Claim Hygiene (Critical)
- [ ] Use wording: `MISRA-aligned checks`, not certified MISRA
- [ ] Use wording: `ASIL-D evidence pipeline`, not ISO certification
- [ ] State clearly when using REST stub vs real SOME/IP service
- [ ] Do not present placeholder metrics as measured metrics

## 7. Slide Artifact Mapping
- [ ] Slide 6 (CARLA): `output/carla_validation.json` + demo screenshot/video
- [ ] Slide 7 (Benchmark): `benchmark_slide7.md` + JSON snippet
- [ ] Slide 8 (OTA + Traceability): `ota_manifest.yaml`, `traceability_matrix.csv`
- [ ] Slide 9 (Metrics): `output/metrics_summary.json` derived from real logs

## 8. Final Submission Gate
- [ ] End-to-end run completed at least once without manual edits
- [ ] All evidence files timestamped from same demo window
- [ ] Team can explain:
  - adversarial loop
  - ASIL checks
  - MISRA checks
  - benchmark methodology
  - limitations and next steps

Hard fail conditions:
- [ ] Any claim that cannot be shown in file evidence
- [ ] Demo path depends on unmentioned manual hacks
- [ ] Numbers in slides do not match generated artifacts
