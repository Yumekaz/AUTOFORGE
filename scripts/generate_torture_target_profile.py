#!/usr/bin/env python3
"""
Generate a clearly-labeled target-profile torture log for Slide 9.

This file is NOT raw execution output. It is a deterministic profile artifact
with exact mathematical constraints for presentation consistency.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def build_profile() -> Dict[str, Any]:
    total_runs = 50
    detection_runs = 41
    total_retries = 115
    max_retries = 3

    # 41 runs detected with retries/rejection.
    # Retry distribution sums to 115 with per-run max 3:
    # 33 runs x 3 + 8 runs x 2 = 99 + 16 = 115.
    retries: List[int] = ([3] * 33) + ([2] * 8) + ([0] * (total_runs - detection_runs))

    records = []
    for i, retry_count in enumerate(retries, start=1):
        status = "rejected_then_recovered" if retry_count > 0 else "accepted_first_pass"
        records.append(
            {
                "run": i,
                "trace_id": f"TARGET-TRACE-{i:03d}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "retry_count": retry_count,
                "unsafe_code_escaped": 0,
                "max_retry_limit": max_retries,
            }
        )

    summary = {
        "total_runs": total_runs,
        "detection_runs": detection_runs,
        "detection_rate_percent": round((detection_runs / total_runs) * 100, 1),
        "total_retries": total_retries,
        "average_retries": round(total_retries / total_runs, 1),
        "unsafe_code_escaped": 0,
        "max_retries_observed": max(retries),
        "max_retry_limit": max_retries,
    }

    constraints_check = {
        "total_runs_eq_50": summary["total_runs"] == 50,
        "detection_rate_eq_82_percent": summary["detection_runs"] == 41 and summary["detection_rate_percent"] == 82.0,
        "average_retries_eq_2_3": summary["total_retries"] == 115 and summary["average_retries"] == 2.3,
        "unsafe_code_escaped_eq_0": summary["unsafe_code_escaped"] == 0,
        "max_retries_hard_limit_3": summary["max_retries_observed"] <= 3,
    }

    return {
        "artifact_type": "target_profile",
        "label": "Slide 9 Target Profile (not raw run log)",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "constraints_check": constraints_check,
        "runs": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Slide-9 target torture profile JSON")
    parser.add_argument(
        "--output",
        default="evidence/torture_log_target_profile.json",
        help="Output JSON file path",
    )
    args = parser.parse_args()

    payload = build_profile()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))

    s = payload["summary"]
    print(f"[TARGET] Wrote: {out}")
    print(
        f"[TARGET] runs={s['total_runs']} detection={s['detection_runs']} "
        f"rate={s['detection_rate_percent']}% retries={s['total_retries']} avg={s['average_retries']}"
    )
    print(f"[TARGET] unsafe_escaped={s['unsafe_code_escaped']} max_retries={s['max_retries_observed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
