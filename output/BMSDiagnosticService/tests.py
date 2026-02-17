import pytest
from unittest.mock import Mock, call

# --- Mock Service Implementation (for testing purposes) ---
# This mock simulates the behavior of the BMSDiagnosticService
# without needing the actual C++ implementation.
# It allows us to control its internal state and observe its outputs and events.

class MockBMSDiagnosticService:
    """
    A mock implementation of the BMSDiagnosticService for testing.
    It simulates the internal state and provides methods to interact with it,
    as well as a mechanism to record emitted events.
    """
    def __init__(self):
        self._battery_soc = 50.0  # Default values
        self._battery_voltage = 12.0
        self._battery_current