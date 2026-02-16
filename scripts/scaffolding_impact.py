#!/usr/bin/env python3
"""
Compute scaffolding reduction metrics from AUTOFORGE outputs.

This script avoids hardcoded/fake baselines. It reports:
1) Generated scaffold LOC
2) Manual baseline LOC required to justify an 80% reduction claim
3) Actual reduction if you provide a manual baseline LOC

Supports both:
- Single service directory (legacy mode)
- Multi-service aggregate mode (competition summary)

Outputs:
- JSON: output/scaffolding_impact.json
- Markdown: output/scaffolding_impact.md
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, List


DEFAULT_CODE_EXTS = {".cpp", ".hpp", ".h", ".c", ".cc", ".py", ".rs", ".kt", ".java"}


def _count_loc(path: Path) -> int:
    lines = 0
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if raw.strip():
            lines += 1
    return lines


def _is_scaffold_file(path: Path, include_tests: bool) -> bool:
    if path.suffix.lower() not in DEFAULT_CODE_EXTS:
        return False
    name = path.name.lower()
    if not include_tests and ("test" in name or name.startswith("tests")):
        return False
    if "mock" in name:
        return False
    return True


def _collect_scaffold_files(service_dir: Path, include_tests: bool) -> List[Path]:
    files: List[Path] = []
    for p in service_dir.rglob("*"):
        if p.is_file() and _is_scaffold_file(p, include_tests):
            files.append(p)
    return sorted(files)


def _build_markdown(report: Dict) -> str:
    lines = [
        "# Scaffolding Impact Report",
        "",
        f"- Mode: `{report['mode']}`",
        f"- Service directories: `{', '.join(report['service_dirs'])}`",
        f"- Included files: `{report['file_count']}`",
        f"- Generated scaffold LOC: `{report['generated_scaffold_loc']}`",
        f"- LOC needed for 80% reduction claim: `{report['manual_loc_needed_for_80pct']}`",
    ]
    if report["manual_baseline_loc"] is not None:
        lines.append(f"- Manual baseline LOC provided: `{report['manual_baseline_loc']}`")
        lines.append(f"- Actual reduction: `{report['actual_reduction_percent']}%`")
        lines.append(f"- Meets 80% claim: `{report['meets_80pct_claim']}`")
    else:
        lines.append("- Manual baseline LOC provided: `None`")
        lines.append("- Actual reduction: `N/A`")
        lines.append("- Meets 80% claim: `N/A`")

    lines.extend(["", "## Included Files", ""])
    for item in report["files"]:
        lines.append(f"- `{item['path']}` ({item['loc']} LOC)")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute scaffolding impact metrics")
    parser.add_argument(
        "--service-dir",
        default="output/BMSDiagnosticService",
        help="Single service output directory to analyze (legacy mode)",
    )
    parser.add_argument(
        "--service-dirs",
        nargs="*",
        default=[],
        help="Multiple service output directories to aggregate",
    )
    parser.add_argument(
        "--auto-services",
        action="store_true",
        help="Use default service set: output/BMSDiagnosticService, output/BMSDiagnosticServiceJava, output/BMSDiagnosticServiceKotlin",
    )
    parser.add_argument(
        "--manual-baseline-loc",
        type=int,
        default=0,
        help="Manual baseline LOC for comparison (optional; 0 means not provided)",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in generated scaffold LOC",
    )
    parser.add_argument(
        "--json-out",
        default="output/scaffolding_impact.json",
        help="JSON output path",
    )
    parser.add_argument(
        "--md-out",
        default="output/scaffolding_impact.md",
        help="Markdown output path",
    )
    args = parser.parse_args()

    service_dirs: List[Path] = []
    if args.auto_services:
        service_dirs = [
            Path("output/BMSDiagnosticService"),
            Path("output/BMSDiagnosticServiceJava"),
            Path("output/BMSDiagnosticServiceKotlin"),
        ]
    elif args.service_dirs:
        service_dirs = [Path(p) for p in args.service_dirs]
    else:
        service_dirs = [Path(args.service_dir)]

    missing_dirs = [str(p) for p in service_dirs if not p.exists()]
    if missing_dirs:
        raise FileNotFoundError(f"Service directories not found: {missing_dirs}")

    files: List[Path] = []
    for service_dir in service_dirs:
        files.extend(_collect_scaffold_files(service_dir, include_tests=args.include_tests))

    # Deduplicate if same file is reached through overlapping dirs.
    files = sorted({str(p): p for p in files}.values(), key=lambda p: str(p))
    file_rows = []
    total_loc = 0
    for f in files:
        loc = _count_loc(f)
        total_loc += loc
        file_rows.append({"path": str(f).replace("\\", "/"), "loc": loc})

    # If generated is 20% of manual, manual = generated / 0.2
    manual_needed_for_80 = int(math.ceil(total_loc / 0.2)) if total_loc > 0 else 0

    manual_baseline_loc = args.manual_baseline_loc if args.manual_baseline_loc > 0 else None
    actual_reduction = None
    meets_80 = None
    if manual_baseline_loc:
        actual_reduction = round((manual_baseline_loc - total_loc) / manual_baseline_loc * 100.0, 2)
        meets_80 = actual_reduction >= 80.0

    report = {
        "mode": "aggregate" if len(service_dirs) > 1 else "single",
        "service_dirs": [str(p).replace("\\", "/") for p in service_dirs],
        "include_tests": bool(args.include_tests),
        "file_count": len(file_rows),
        "generated_scaffold_loc": total_loc,
        "manual_loc_needed_for_80pct": manual_needed_for_80,
        "manual_baseline_loc": manual_baseline_loc,
        "actual_reduction_percent": actual_reduction,
        "meets_80pct_claim": meets_80,
        "files": file_rows,
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(report, indent=2))
    md_out.write_text(_build_markdown(report))

    print(f"[IMPACT] Wrote JSON report: {json_out}")
    print(f"[IMPACT] Wrote Markdown report: {md_out}")
    print(f"[IMPACT] Generated scaffold LOC: {total_loc}")
    print(f"[IMPACT] Manual LOC required for 80% claim: {manual_needed_for_80}")
    if manual_baseline_loc:
        print(f"[IMPACT] Actual reduction: {actual_reduction}%")
        print(f"[IMPACT] Meets 80% claim: {meets_80}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
