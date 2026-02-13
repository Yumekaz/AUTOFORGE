#!/usr/bin/env python3
"""
Benchmark AUTOFORGE across multiple LLMs.

Runs the pipeline N times per provider and captures:
  - MISRA compliance
  - ASIL-D compliance
  - Compilation status
  - Retry count
  - Latency

Use --dry-run to generate deterministic mock results without APIs.
"""

import argparse
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, List

import yaml

# Add src to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pipeline.orchestrator import Pipeline
from pipeline.validation_gate import get_validation_gate


def _load_language(requirement_path: Path) -> str:
    data = yaml.safe_load(requirement_path.read_text())
    return data.get("service", {}).get("language", "cpp")


def _mock_run(provider: str, run_index: int) -> Dict[str, Any]:
    # Deterministic mock data for CI/testing
    latency_ms = 900 + (run_index * 17)
    retries = run_index % 2
    return {
        "provider": provider,
        "run": run_index + 1,
        "success": True,
        "retry_count": retries,
        "latency_ms": latency_ms,
        "misra_pass": True,
        "asil_pass": True,
        "compilation_pass": True,
        "issues_count": 0,
    }


def _summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    if total == 0:
        return {}
    success_rate = sum(1 for r in results if r["success"]) / total
    avg_latency = sum(r["latency_ms"] for r in results) / total
    avg_retries = sum(r["retry_count"] for r in results) / total
    misra_rate = sum(1 for r in results if r["misra_pass"]) / total
    asil_rate = sum(1 for r in results if r["asil_pass"]) / total
    compile_rate = sum(1 for r in results if r["compilation_pass"]) / total

    return {
        "runs": total,
        "success_rate": round(success_rate, 3),
        "avg_latency_ms": round(avg_latency, 1),
        "avg_retries": round(avg_retries, 2),
        "misra_pass_rate": round(misra_rate, 3),
        "asil_pass_rate": round(asil_rate, 3),
        "compilation_pass_rate": round(compile_rate, 3),
    }


def _markdown_table(summary: Dict[str, Dict[str, Any]]) -> str:
    headers = [
        "Provider", "Runs", "Success", "Avg Latency (ms)",
        "Avg Retries", "MISRA Pass", "ASIL-D Pass", "Compile Pass"
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for provider, stats in summary.items():
        lines.append(
            "| "
            + " | ".join([
                provider,
                str(stats.get("runs", 0)),
                str(stats.get("success_rate", 0)),
                str(stats.get("avg_latency_ms", 0)),
                str(stats.get("avg_retries", 0)),
                str(stats.get("misra_pass_rate", 0)),
                str(stats.get("asil_pass_rate", 0)),
                str(stats.get("compilation_pass_rate", 0)),
            ])
            + " |"
        )
    return "\n".join(lines)


def _slide7_markdown_table(summary: Dict[str, Dict[str, Any]]) -> str:
    headers = [
        "LLM", "MISRA Pass", "ASIL-D Checks", "Compilation",
        "Avg Retries", "Latency"
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for provider, stats in summary.items():
        lines.append(
            "| "
            + " | ".join([
                provider,
                f\"{int(stats.get('misra_pass_rate', 0) * 100)}%\",
                f\"{int(stats.get('asil_pass_rate', 0) * 100)}%\",
                f\"{int(stats.get('compilation_pass_rate', 0) * 100)}%\",
                str(stats.get("avg_retries", 0)),
                f\"{stats.get('avg_latency_ms', 0)}ms\",
            ])
            + " |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="AUTOFORGE LLM Benchmark")
    parser.add_argument("--requirement", default="input/requirements/bms_diagnostic.yaml")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--providers", default="gemini,ollama,groq")
    parser.add_argument("--output", default="benchmark_results.json")
    parser.add_argument("--markdown-out", default="benchmark_results.md")
    parser.add_argument("--slide7-out", default="benchmark_slide7.md")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    requirement_path = Path(args.requirement)
    language = _load_language(requirement_path)
    providers = [p.strip() for p in args.providers.split(",") if p.strip()]

    all_results: Dict[str, List[Dict[str, Any]]] = {}
    for provider in providers:
        provider_results = []
        for i in range(args.runs):
            if args.dry_run:
                provider_results.append(_mock_run(provider, i))
                continue

            pipeline = Pipeline(llm_provider=provider)
            start = time.time()
            result = pipeline.run(str(requirement_path))
            end = time.time()

            validation = {}
            misra_pass = False
            asil_pass = False
            compilation_pass = False
            issues_count = 0

            if result.generated_code and result.test_code:
                gate = get_validation_gate()
                validation = gate.validate(result.generated_code, result.test_code, language)
                compilation_pass = validation.get("static_analysis", {}).get("compilation") == "PASS"
                misra_pass = validation.get("misra_compliance", {}).get("clang_tidy") == "PASS"
                asil_pass = validation.get("asil_d_compliance", {}).get("status") == "PASS"
                issues_count = len(validation.get("issues", []))

            provider_results.append({
                "provider": provider,
                "run": i + 1,
                "success": result.success,
                "retry_count": result.retry_count,
                "latency_ms": int((end - start) * 1000),
                "misra_pass": misra_pass,
                "asil_pass": asil_pass,
                "compilation_pass": compilation_pass,
                "issues_count": issues_count,
            })

        all_results[provider] = provider_results

    summary = {p: _summarize(r) for p, r in all_results.items()}

    output = {
        "meta": {
            "runs_per_provider": args.runs,
            "providers": providers,
            "requirement": str(requirement_path),
            "language": language,
            "dry_run": args.dry_run,
        },
        "results": all_results,
        "summary": summary,
    }

    Path(args.output).write_text(json.dumps(output, indent=2))
    Path(args.markdown_out).write_text(_markdown_table(summary))
    Path(args.slide7_out).write_text(_slide7_markdown_table(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
