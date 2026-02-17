"""
REST transport adapter for AUTOFORGE service calls.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict

from transport.transport_interface import Transport


class RestTransport(Transport):
    """HTTP JSON transport for local validation service."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def send_bms_signals(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/bms/diagnostics"
        payload = json.dumps(signals).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
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
