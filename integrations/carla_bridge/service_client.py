"""
Service Client for AUTOFORGE CARLA Integration

Supports REST (default) and mock SOME/IP placeholder.
"""

from __future__ import annotations

import json
from typing import Dict, Any
import urllib.request
import urllib.error


class ServiceClient:
    """Lightweight client to call generated services."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def send_bms_signals(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send signals to a REST BMS endpoint.
        Expected endpoint: POST {base_url}/bms/diagnostics
        """
        url = f"{self.base_url}/bms/diagnostics"
        payload = json.dumps(signals).encode("utf-8")
        request = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            return {"error": f"HTTP {e.code}", "details": body}
        except urllib.error.URLError as e:
            return {"error": "Connection failed", "details": str(e)}
