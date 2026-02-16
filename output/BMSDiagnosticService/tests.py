import pytest
from unittest.mock import MagicMock, patch

# Mock class for the BMSDiagnosticService
# This mock will simulate the behavior of the service based on its internal state
# and emit events.
class MockBMSDiagnosticService:
    """
    A mock implementation of the BMSDiagnosticService for testing purposes.
    It simulates internal battery state and event emission logic.
    """
    def __init__(self):
        self._battery_soc = 0.0
        self._battery_voltage = 0.0
        self._battery_current = 0.0
        self._battery_temperature = 0.0
        self._cell_voltages = []
        self.emitted_events = []