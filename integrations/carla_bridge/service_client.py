"""
Service Client for AUTOFORGE CARLA Integration

Protocol Abstraction:
- REST transport (default, active validation path)
- SOME/IP transport placeholder (generated middleware mapping path)
"""

from __future__ import annotations

import os
import sys
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from transport import RestTransport, SomeIpTransport, Transport


class ServiceClient:
    """Lightweight client to call generated services."""

    def __init__(self, base_url: str, transport: str = "rest"):
        self.base_url = base_url.rstrip("/")
        self.transport_name = transport.lower()
        self.transport: Transport = self._init_transport(self.transport_name)

    def _init_transport(self, transport: str) -> Transport:
        if transport == "someip":
            return SomeIpTransport(self.base_url)
        return RestTransport(self.base_url)

    def send_bms_signals(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Send signals using configured transport adapter."""
        return self.transport.send_bms_signals(signals)
