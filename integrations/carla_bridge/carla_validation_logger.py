"""
CARLA Validation Logger

Collects CARLA simulation data, service responses, and latency metrics.
Outputs a JSON log for Round 2 evidence.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Any, List


class CarlaValidationLogger:
    """Capture and export CARLA validation evidence."""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.records: List[Dict[str, Any]] = []
        self.start_ts = time.time()

    def log(
        self,
        signals: Dict[str, Any],
        response: Dict[str, Any],
        latency_ms: float,
    ) -> None:
        entry = {
            "timestamp_s": round(time.time() - self.start_ts, 3),
            "signals": {
                "vehicle_speed": signals.get("vehicle_speed"),
                "battery_soc": signals.get("battery_soc"),
                "battery_temperature": signals.get("battery_temperature"),
                "tire_pressure_fl": signals.get("tire_pressure_fl"),
                "tire_pressure_fr": signals.get("tire_pressure_fr"),
                "tire_pressure_rl": signals.get("tire_pressure_rl"),
                "tire_pressure_rr": signals.get("tire_pressure_rr"),
            },
            "response": response,
            "latency_ms": round(latency_ms, 2),
        }
        self.records.append(entry)

    def summarize(self) -> Dict[str, Any]:
        if not self.records:
            return {
                "total_samples": 0,
                "avg_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
            }

        latencies = sorted(r["latency_ms"] for r in self.records)
        avg_latency = sum(latencies) / len(latencies)
        p95_index = int(0.95 * (len(latencies) - 1))
        return {
            "total_samples": len(self.records),
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": latencies[p95_index],
        }

    def save(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": self.summarize(),
            "records": self.records,
        }
        self.output_path.write_text(json.dumps(payload, indent=2))
