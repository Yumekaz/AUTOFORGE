#!/usr/bin/env python3
"""
Torture test runner for AUTOFORGE.

Runs pipeline repeatedly across multiple requirement YAML files and records:
- duration per run
- retry count
- pass/fail

Outputs:
- evidence/torture_log.json
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pipeline.orchestrator import Pipeline  # noqa: E402


DEFAULT_REQUIREMENTS = [
    "input/requirements/bms_diagnostic.yaml",
    "input/requirements/tire_pressure_diagnostic.yaml",
    "input/requirements/motor_health_diagnostic.yaml",
    "input/requirements/bms_diagnostic_with_ml.yaml",
]


def _build_run_plan(requirements: List[str], total_runs: int, seed: int) -> List[str]:
    rng = random.Random(seed)
    plan = []
    for i in range(total_runs):
        plan.append(requirements[i % len(requirements)])
    rng.shuffle(plan)
    return plan


def _safe_rate(n: int, d: int) -> float:
    return round((n / d) * 100.0, 2) if d else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AUTOFORGE torture test")
    parser.add_argument("--provider", default="ollama", help="LLM provider (ollama, gemini, mock)")
    parser.add_argument("--runs", type=int, default=20, help="Total number of runs")
    parser.add_argument(
        "--requirements",
        default=",".join(DEFAULT_REQUIREMENTS),
        help="Comma-separated requirement YAML paths",
    )
    parser.add_argument("--seed", type=int, default=42, help="Shuffle seed for run order")
    parser.add_argument("--output", default="evidence/torture_log.json", help="Output log JSON path")
    parser.add_argument("--output-dir", default="output", help="Pipeline output directory")
    args = parser.parse_args()

    requirements = [x.strip() for x in args.requirements.split(",") if x.strip()]
    missing = [r for r in requirements if not (ROOT / r).exists()]
    if missing:
        raise FileNotFoundError(f"Missing requirement files: {missing}")

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONWARNINGS", "ignore::FutureWarning")

    plan = _build_run_plan(requirements, args.runs, args.seed)
    runs: List[Dict] = []

    started = time.time()
    for idx, req in enumerate(plan, start=1):
        print(f"[TORTURE] Run {idx}/{args.runs} | provider={args.provider} | requirement={req}")
        pipeline = Pipeline(llm_provider=args.provider, output_dir=args.output_dir)
        t0 = time.time()
        result = pipeline.run(str(ROOT / req))
        t1 = time.time()

        run_item = {
            "run_index": idx,
            "requirement": req,
            "provider": args.provider,
            "success": bool(result.success),
            "retry_count": int(result.retry_count),
            "duration_sec": round(t1 - t0, 3),
            "trace_id": result.trace_id,
            "timestamp": result.timestamp,
            "errors": list(result.errors),
        }
        runs.append(run_item)

    ended = time.time()
    success_count = sum(1 for r in runs if r["success"])
    fail_count = len(runs) - success_count
    avg_duration = round(sum(r["duration_sec"] for r in runs) / len(runs), 3) if runs else 0.0
    avg_retry = round(sum(r["retry_count"] for r in runs) / len(runs), 3) if runs else 0.0

    by_requirement: Dict[str, Dict] = {}
    for req in requirements:
        subset = [r for r in runs if r["requirement"] == req]
        if not subset:
            continue
        ok = sum(1 for r in subset if r["success"])
        by_requirement[req] = {
            "runs": len(subset),
            "success_rate_percent": _safe_rate(ok, len(subset)),
            "avg_duration_sec": round(sum(r["duration_sec"] for r in subset) / len(subset), 3),
            "avg_retry_count": round(sum(r["retry_count"] for r in subset) / len(subset), 3),
        }

    report = {
        "meta": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "provider": args.provider,
            "runs": args.runs,
            "seed": args.seed,
            "requirements": requirements,
            "total_wall_time_sec": round(ended - started, 3),
        },
        "summary": {
            "success_count": success_count,
            "fail_count": fail_count,
            "success_rate_percent": _safe_rate(success_count, len(runs)),
            "avg_duration_sec": avg_duration,
            "avg_retry_count": avg_retry,
        },
        "by_requirement": by_requirement,
        "runs": runs,
    }

    out_path = ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n[TORTURE] Completed")
    print(f"[TORTURE] Output: {out_path}")
    print(f"[TORTURE] Success rate: {report['summary']['success_rate_percent']}%")
    print(f"[TORTURE] Avg duration: {report['summary']['avg_duration_sec']} sec")
    print(f"[TORTURE] Avg retries: {report['summary']['avg_retry_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

