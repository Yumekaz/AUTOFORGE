#!/usr/bin/env python3
"""
Verify strict C++ compliance path (compile + clang-tidy + cppcheck + ASIL heuristics).

This provides a deterministic evidence artifact for compliance tooling readiness.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pipeline.validation_gate import get_validation_gate  # noqa: E402


REFERENCE_CPP = r"""
#include <cstddef>
#include <cstdint>
#include <vector>

namespace compliance_ref {

enum class Status : std::uint8_t {
    Ok = 0U,
    Warning = 1U,
    Critical = 2U
};

struct BatteryStatus {
    float soc;
    float voltage;
    float current;
    float temperature;
    Status health;
};

class BmsServiceRef {
public:
    BmsServiceRef() = default;

    // cppcheck-suppress unusedFunction
    bool get_status(BatteryStatus& out) const {
        if (!is_initialized_) {
            return false;
        }

        out.soc = soc_;
        out.voltage = voltage_;
        out.current = current_;
        out.temperature = temperature_;
        out.health = evaluate_health(temperature_, soc_);
        return true;
    }

    // cppcheck-suppress unusedFunction
    bool update_cells(const std::vector<float>& cell_v) {
        if (cell_v.empty()) {
            return false;
        }
        if (cell_v.size() > cells_.size()) {
            return false;
        }

        for (std::size_t i = 0U; i < cell_v.size(); ++i) {
            cells_.at(i) = cell_v.at(i);
        }
        is_initialized_ = true;
        return true;
    }

    // cppcheck-suppress unusedFunction
    void update_telemetry(float soc, float voltage, float current, float temp) {
        soc_ = clamp(soc, 0.0F, 100.0F);
        voltage_ = clamp(voltage, 200.0F, 500.0F);
        current_ = clamp(current, -500.0F, 500.0F);
        temperature_ = clamp(temp, -40.0F, 120.0F);
        is_initialized_ = true;
    }

private:
    static float clamp(float value, float low, float high) {
        if (value < low) {
            return low;
        }
        if (value > high) {
            return high;
        }
        return value;
    }

    static Status evaluate_health(float temp, float soc) {
        if (temp > 60.0F) {
            return Status::Critical;
        }
        if ((temp > 45.0F) || (soc < 20.0F)) {
            return Status::Warning;
        }
        return Status::Ok;
    }

    std::vector<float> cells_ {16U, 0.0F};
    float soc_ {0.0F};
    float voltage_ {0.0F};
    float current_ {0.0F};
    float temperature_ {0.0F};
    bool is_initialized_ {false};
};

}  // namespace compliance_ref
"""


def main() -> int:
    os.environ["AUTOFORGE_STRICT_VALIDATION"] = "1"
    os.environ["AUTOFORGE_MIN_SERVICE_LINES"] = "40"
    os.environ["AUTOFORGE_CXX"] = r"C:\MinGW\bin\g++.exe"

    gate = get_validation_gate()
    result = gate.validate(REFERENCE_CPP, "", "cpp")

    out = {
        "strict_mode": True,
        "min_service_lines": 40,
        "result": result,
        "passed": bool(result.get("valid", False)),
    }

    out_path = ROOT / "output" / "strict_cpp_compliance_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))

    print(f"[STRICT] Report written: {out_path}")
    print(f"[STRICT] valid={out.get('passed')}")
    return 0 if out.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
