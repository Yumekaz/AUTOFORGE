"""
Transport abstraction interface for AUTOFORGE runtime adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class Transport(ABC):
    """Protocol-agnostic request/response transport."""

    @abstractmethod
    def send_bms_signals(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
