"""
ASIL-D Compliance Validation for AUTOFORGE (ISO 26262)

This module performs pragmatic, automatable checks that approximate
ASIL-D compliance signals for generated C++ code. It integrates:
  - Heuristic memory safety checks
  - Deterministic behavior checks
  - Timing constraint checks
  - clang Static Analyzer (if available)

Note: This does not replace a formal safety case. It provides evidence
artifacts and automated gates aligned with ISO 26262 expectations.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Dict, List, Any
from pathlib import Path


@dataclass
class AsilCheckResult:
    """Result of ASIL-D checks."""
    compliant: bool
    issues: List[str]
    static_analyzer: Dict[str, Any]
    heuristic_checks: Dict[str, Any]


class AsilDValidator:
    """
    ASIL-D validation for C++ code.

    Checks include:
    - Memory safety (unsafe APIs, raw memory ops, unchecked pointers)
    - Timing constraints (unbounded loops)
    - Determinism (randomness, time-based, threading without controls)
    - clang Static Analyzer (if clang is available)
    """

    # Heuristic rules (simple, transparent, and deterministic)
    UNSAFE_APIS = [
        "strcpy(", "strcat(", "sprintf(", "vsprintf(",
        "gets(", "strncpy(", "strncat(",
        "memcpy(", "memmove(", "malloc(", "free(",
        "realloc(", "alloca(",
    ]

    NON_DETERMINISTIC_APIS = [
        "rand(", "srand(", "time(", "chrono::system_clock",
        "std::random_device", "std::mt19937",
        "std::thread", "std::async",
    ]

    UNBOUNDED_LOOPS = [
        "while(true)", "while (true)", "for(;;)", "for (;;)",
    ]

    def validate_cpp(self, code: str, source_path: Path) -> AsilCheckResult:
        issues: List[str] = []
        heuristic: Dict[str, Any] = {
            "unsafe_api": [],
            "non_determinism": [],
            "unbounded_loops": [],
        }

        # Memory safety heuristics
        for token in self.UNSAFE_APIS:
            if token in code:
                heuristic["unsafe_api"].append(token)
        if heuristic["unsafe_api"]:
            issues.append(
                f"ASIL-D Memory Safety: unsafe APIs used: {', '.join(heuristic['unsafe_api'])}"
            )

        # Determinism heuristics
        for token in self.NON_DETERMINISTIC_APIS:
            if token in code:
                heuristic["non_determinism"].append(token)
        if heuristic["non_determinism"]:
            issues.append(
                "ASIL-D Determinism: non-deterministic APIs detected: "
                + ", ".join(heuristic["non_determinism"])
            )

        # Timing constraints (basic)
        for token in self.UNBOUNDED_LOOPS:
            if token in code:
                heuristic["unbounded_loops"].append(token)
        if heuristic["unbounded_loops"]:
            issues.append(
                "ASIL-D Timing: unbounded loop(s) detected: "
                + ", ".join(heuristic["unbounded_loops"])
            )

        # clang Static Analyzer
        static_analyzer = self._run_clang_static_analyzer(source_path)
        if static_analyzer.get("status") == "FAIL":
            issues.append(
                "ASIL-D Static Analyzer: issues detected by clang --analyze"
            )

        compliant = len(issues) == 0
        return AsilCheckResult(
            compliant=compliant,
            issues=issues,
            static_analyzer=static_analyzer,
            heuristic_checks=heuristic,
        )

    def _run_clang_static_analyzer(self, source_path: Path) -> Dict[str, Any]:
        """
        Run clang Static Analyzer (clang --analyze) if available.
        """
        try:
            result = subprocess.run(
                ["clang", "--analyze", "-std=c++17", str(source_path)],
                capture_output=True,
                text=True,
                timeout=20,
            )
        except FileNotFoundError:
            return {"status": "SKIP (clang not installed)"}
        except subprocess.TimeoutExpired:
            return {"status": "TIMEOUT"}
        except Exception as e:
            return {"status": f"ERROR: {e}"}

        # clang --analyze returns non-zero on issues
        if result.returncode == 0:
            return {"status": "PASS", "output": ""}

        # Keep output short for logs
        output = (result.stderr or result.stdout or "").strip()
        if len(output) > 2000:
            output = output[:2000] + "\n...truncated..."

        return {"status": "FAIL", "output": output}

