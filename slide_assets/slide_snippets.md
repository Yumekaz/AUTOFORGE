# Slide Snippets (Copy/Paste)

## Slide 6: CARLA Simulation & ASIL Validation
- Input: Real-time CARLA signals (Speed, Tyre, SoC) via SOME/IP/REST
- ASIL Context: Safety monitoring at ASIL-D level (highest integrity)
- Output: <10ms prediction latency, containerized ASIL-D service
- Evidence: `output/carla_validation.json`

## Slide 7: Multi-LLM Benchmarking
- Evidence: `benchmark_results.json`
- Slide Table: `benchmark_slide7.md`

## Slide 8: Variants & Subscription OTA
- Evidence: `output/<Service>/ota_manifest.yaml`
- Subscription config: `config/subscription_config.yaml`

## Slide 9: Metrics & Resilience
- Evidence: `output/metrics_summary.json`
