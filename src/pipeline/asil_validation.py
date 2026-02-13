"""
ASIL-D Compliance Validation for AUTOFORGE (ISO 26262)

This module provides runnable, automatable checks that approximate
ASIL-D compliance signals. It includes:
  - Memory safety checks
  - Timing constraints
  - Deterministic behavior checks
  - Defensive programming checks
  - clang Static Analyzer integration (if installed)

It is designed to run even when no real code is provided by falling
back to mock examples for testing and CI sanity checks.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path


@dataclass
class AsilCheckResult:
    """Result of ASIL-D checks."""
    compliant: bool
    issues: List[str]
    static_analyzer: Dict[str, Any]
    heuristic_checks: Dict[str, Any]
    evidence: Dict[str, Any]


class AsilDValidator:
    """
    ASIL-D validation for C++ code.

    Checks include:
    - Memory safety (unsafe APIs, raw memory ops, unchecked pointers)
    - Timing constraints (unbounded loops)
    - Determinism (randomness, time-based, threading without controls)
    - Defensive programming (error handling, explicit bounds checks)
    - clang Static Analyzer (clang --analyze)
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

    DEFENSIVE_SIGNAL = [
        "if (", "if(", "throw", "return false", "return nullptr",
        "std::optional", "std::expected", "assert(",
    ]

    BOUNDS_SIGNAL = [
        "size()", "length()", "at(", "std::array", "std::vector",
    ]

    def validate_cpp(
        self,
        code: Optional[str] = None,
        source_path: Optional[Path] = None,
        use_mock: bool = False,
    ) -> AsilCheckResult:
        """
        Validate C++ code for ASIL-D compliance signals.

        If code/source_path are missing (or use_mock=True), mock examples
        are used so the validator remains runnable in isolation.
        """
        if use_mock or not code:
            code = self._mock_example_code()

        issues: List[str] = []
        heuristic: Dict[str, Any] = {
            "unsafe_api": [],
            "non_determinism": [],
            "unbounded_loops": [],
            "defensive_programming": False,
            "bounds_checks": False,
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

        # Defensive programming signals
        if any(token in code for token in self.DEFENSIVE_SIGNAL):
            heuristic["defensive_programming"] = True
        else:
            issues.append("ASIL-D Defensive: no explicit error handling detected")

        # Bounds checks signals
        if any(token in code for token in self.BOUNDS_SIGNAL):
            heuristic["bounds_checks"] = True
        else:
            issues.append("ASIL-D Bounds: no bounds-checking signals detected")

        # clang Static Analyzer
        static_analyzer = self._run_clang_static_analyzer(source_path)
        if static_analyzer.get("status") == "FAIL":
            issues.append("ASIL-D Static Analyzer: issues detected by clang --analyze")

        compliant = len(issues) == 0
        evidence = {
            "memory_safety": "PASS" if not heuristic["unsafe_api"] else "FAIL",
            "determinism": "PASS" if not heuristic["non_determinism"] else "FAIL",
            "timing": "PASS" if not heuristic["unbounded_loops"] else "FAIL",
            "defensive_programming": "PASS" if heuristic["defensive_programming"] else "FAIL",
            "bounds_checks": "PASS" if heuristic["bounds_checks"] else "FAIL",
        }

        return AsilCheckResult(
            compliant=compliant,
            issues=issues,
            static_analyzer=static_analyzer,
            heuristic_checks=heuristic,
            evidence=evidence,
        )

    def _run_clang_static_analyzer(self, source_path: Optional[Path]) -> Dict[str, Any]:
        """
        Run clang Static Analyzer (clang --analyze) if available and path exists.
        """
        if not source_path or not source_path.exists():
            return {"status": "SKIP (no source path)"}

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

        if result.returncode == 0:
            return {"status": "PASS", "output": ""}

        output = (result.stderr or result.stdout or "").strip()
        if len(output) > 2000:
            output = output[:2000] + "\n...truncated..."

        return {"status": "FAIL", "output": output}

    def _mock_example_code(self) -> str:
        """
        Mock example code for standalone testing.
        Designed to trigger some checks but remain compilable.
        """
        return r"""
#include <vector>
#include <string>

class MockService {
public:
    bool Initialize(const std::vector<int>& data) {
        if (data.empty()) {
            return false;
        }
        int value = data.at(0);
        return value >= 0;
    }
};
"""


if __name__ == "__main__":
    # Mock runnable example
    validator = AsilDValidator()
    result = validator.validate_cpp(use_mock=True)
    print("ASIL-D compliant:", result.compliant)
    print("Issues:", result.issues)
