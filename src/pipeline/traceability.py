"""
ASPICE Traceability Matrix Generator (SWE.3)

Generates a requirement -> test -> code traceability matrix
in CSV and YAML formats.
"""

from __future__ import annotations

import re
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List


@dataclass
class TraceabilityRow:
    requirement_id: str
    requirement_desc: str
    test_cases: List[str]
    code_artifacts: List[str]
    aspice_reference: str


class TraceabilityMatrix:
    """Build and persist an ASPICE SWE.3 traceability matrix."""

    def build(
        self,
        requirement: Dict[str, Any],
        test_code: str,
        code: str,
    ) -> List[TraceabilityRow]:
        service = requirement.get("service", {})
        trace = requirement.get("traceability", {})
        aspice_ref = trace.get("aspice_reference", "SWE.3")

        requirements = self._extract_requirements(requirement)
        tests = self._extract_tests(test_code)
        artifacts = self._extract_code_artifacts(requirement, code)

        rows: List[TraceabilityRow] = []
        for req_id, req_desc in requirements:
            rows.append(
                TraceabilityRow(
                    requirement_id=req_id,
                    requirement_desc=req_desc,
                    test_cases=tests,
                    code_artifacts=artifacts,
                    aspice_reference=aspice_ref,
                )
            )
        if not rows:
            rows.append(
                TraceabilityRow(
                    requirement_id=trace.get("requirement_id", "REQ-UNKNOWN"),
                    requirement_desc=service.get("description", "Unknown requirement"),
                    test_cases=tests,
                    code_artifacts=artifacts,
                    aspice_reference=aspice_ref,
                )
            )
        return rows

    def save_csv(self, rows: List[TraceabilityRow], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "requirement_id",
                "requirement_desc",
                "test_cases",
                "code_artifacts",
                "aspice_reference",
            ])
            for row in rows:
                writer.writerow([
                    row.requirement_id,
                    row.requirement_desc,
                    ";".join(row.test_cases),
                    ";".join(row.code_artifacts),
                    row.aspice_reference,
                ])

    def save_yaml(self, rows: List[TraceabilityRow], output_path: Path) -> None:
        import yaml
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "requirement_id": r.requirement_id,
                "requirement_desc": r.requirement_desc,
                "test_cases": r.test_cases,
                "code_artifacts": r.code_artifacts,
                "aspice_reference": r.aspice_reference,
            }
            for r in rows
        ]
        with open(output_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def _extract_requirements(self, requirement: Dict[str, Any]) -> List[tuple]:
        trace = requirement.get("traceability", {})
        base_id = trace.get("requirement_id", "REQ-UNKNOWN")
        rows = []

        rules = requirement.get("rules", [])
        for idx, rule in enumerate(rules, start=1):
            rid = f"{base_id}-RULE-{idx:03d}"
            desc = f"{rule.get('name', 'rule')} | {rule.get('condition', '')}"
            rows.append((rid, desc))

        methods = requirement.get("service", {}).get("interface", {}).get("methods", [])
        for idx, method in enumerate(methods, start=1):
            rid = f"{base_id}-API-{idx:03d}"
            desc = f"Method {method.get('name', 'UnknownMethod')}"
            rows.append((rid, desc))

        return rows

    def _extract_tests(self, test_code: str) -> List[str]:
        tests = []
        tests.extend(re.findall(r"def\s+(test_[a-zA-Z0-9_]+)\s*\(", test_code))
        tests.extend(re.findall(r"TEST\(\s*([A-Za-z0-9_]+)\s*,\s*([A-Za-z0-9_]+)\s*\)", test_code))
        # Normalize gtest to Suite.Test
        normalized = []
        for t in tests:
            if isinstance(t, tuple):
                normalized.append(f"{t[0]}.{t[1]}")
            else:
                normalized.append(t)
        return sorted(set(normalized))

    def _extract_code_artifacts(self, requirement: Dict[str, Any], code: str) -> List[str]:
        artifacts = []
        methods = requirement.get("service", {}).get("interface", {}).get("methods", [])
        for method in methods:
            name = method.get("name")
            if name:
                artifacts.append(name)

        # Also capture class name if present
        class_match = re.findall(r"class\s+([A-Za-z0-9_]+)", code)
        for c in class_match:
            artifacts.append(c)

        return sorted(set(artifacts))

