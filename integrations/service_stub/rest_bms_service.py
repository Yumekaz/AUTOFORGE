#!/usr/bin/env python3
"""
Minimal REST BMS Service Stub for CARLA Integration

Endpoint:
  POST /bms/diagnostics

This stub is deterministic and can run on a CPU-only machine.
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Any


def _evaluate_bms(signals: Dict[str, Any]) -> Dict[str, Any]:
    soc = float(signals.get("battery_soc", 0.0))
    temp = float(signals.get("battery_temperature", 0.0))
    tire_pressure_fl = float(signals.get("tire_pressure_fl", 0.0))
    vehicle_speed = float(signals.get("vehicle_speed", 0.0))
    ml_score = float(signals.get("ml_inference_score", signals.get("failure_score", 0.0)))
    warnings = []
    health_status = 0

    if soc < 20.0:
        health_status = max(health_status, 1)
        warnings.append({"code": 0x0001, "message": "Low battery"})
    if temp > 45.0:
        health_status = max(health_status, 1)
        warnings.append({"code": 0x0002, "message": "High temperature"})
    if temp > 60.0:
        health_status = max(health_status, 2)
        warnings.append({"code": 0x0003, "message": "Critical temperature - shutdown required"})

    if tire_pressure_fl < 2.0 and vehicle_speed > 80.0:
        health_status = max(health_status, 2)
        warnings.append(
            {
                "code": "0x0004",
                "message": "Critical: Low tire pressure at high speed - failure risk detected",
            }
        )

    if ml_score > 0.5:
        health_status = max(health_status, 2)
        warnings.append(
            {
                "code": "0x0005",
                "message": "ML: Tire failure probability elevated (score > 0.5)",
            }
        )

    return {"health_status": health_status, "warnings": warnings}


_latest_lock = threading.Lock()
_latest_payload: Dict[str, Any] = {
    "timestamp_unix": 0.0,
    "signals": {},
    "response": {"health_status": 0, "warnings": []},
}


def _set_latest(signals: Dict[str, Any], response: Dict[str, Any]) -> None:
    with _latest_lock:
        _latest_payload["timestamp_unix"] = time.time()
        _latest_payload["signals"] = signals
        _latest_payload["response"] = response


def _get_latest() -> Dict[str, Any]:
    with _latest_lock:
        return dict(_latest_payload)


class BmsHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            payload = {"status": "ok"}
        elif self.path == "/bms/latest":
            payload = _get_latest()
        else:
            self.send_response(404)
            self.end_headers()
            return

        response_bytes = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_POST(self):  # noqa: N802
        if self.path != "/bms/diagnostics":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        response = _evaluate_bms(payload)
        _set_latest(payload, response)
        response_bytes = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def log_message(self, format, *args):  # noqa: A003
        return


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 30509), BmsHandler)
    print("REST BMS stub running on http://0.0.0.0:30509")
    server.serve_forever()


if __name__ == "__main__":
    main()
