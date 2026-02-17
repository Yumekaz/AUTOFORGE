import pytest
from unittest.mock import Mock, patch

# Mocking the SOME/IP service implementation
class TirePressureDiagnosticService:
    def __init__(self):
        self.tire_pressure_fl = 0.0
        self.tire_pressure_fr = 0.0
        self.tire_pressure_rl = 0.0
        self.tire_pressure_rr = 0.0
        self.vehicle_speed = 0.0
        self.ambient_temperature = 0.0

    def GetTireStatus(self):
        return {
            "tire_pressure_fl": self.tire_pressure_fl,
            "tire_pressure_fr": self.tire_pressure_fr,
            "tire_pressure_rl": self.tire_pressure_rl,
            "tire_pressure_rr": self.tire_pressure_rr,
            "failure_risk": 0.0
        }

    def emit_warning(self, code, msg):
        print(f"Warning: {code} - {msg}")

# Test cases for the TirePressureDiagnosticService

def test_get_tire_status():
    """
    Verify that GetTireStatus returns the correct tire pressures and failure risk.
    """
    service = TirePressureDiagnosticService()
    service.tire_pressure_fl = 3.0
    service.tire_pressure_fr = 2.5
    service.tire_pressure_rl = 2.8
    service.tire_pressure_rr = 2.7

    result = service.GetTireStatus()

    assert result["tire_pressure_fl"] == 3.0
    assert result["tire_pressure_fr"] == 2.5
    assert result["tire_pressure_rl"] == 2.8
    assert result["tire_pressure_rr"] == 2.7
    assert result["failure_risk"] == 0.0

def test_low_pressure_warning():
    """
    Verify that the low pressure warning is emitted when any tire pressure is below 2.0.
    """
    service = TirePressureDiagnosticService()
    service.tire_pressure_fl = 1.9
    service.tire_pressure_fr = 2.5
    service.tire_pressure_rl = 2.8
    service.tire_pressure_rr = 2.7

    with patch.object(service, 'emit_warning') as mock_emit:
        service.GetTireStatus()

    mock_emit.assert_called_once_with(0x0101, 'Low tire pressure')

def test_imbalance_warning():
    """
    Verify that the imbalance warning is emitted when there is a significant difference in tire pressures.
    """
    service = TirePressureDiagnosticService()
    service.tire_pressure_fl = 2.5
    service.tire_pressure_fr = 2.1
    service.tire_pressure_rl = 2.8
    service.tire_pressure_rr = 2.7

    with patch.object(service, 'emit_warning') as mock_emit:
        service.GetTireStatus()

    mock_emit.assert_called_once_with(0x0102, 'Tire pressure imbalance')

def test_get_tire_status_null_inputs():
    """
    Verify that GetTireStatus handles null inputs gracefully.
    """
    service = TirePressureDiagnosticService()
    service.tire_pressure_fl = None
    service.tire_pressure_fr = 2.5
    service.tire_pressure_rl = 2.8
    service.tire_pressure_rr = 2.7

    with pytest.raises(ValueError):
        service.GetTireStatus()

def test_get_tire_status_empty_values():
    """
    Verify that GetTireStatus handles empty values gracefully.
    """
    service = TirePressureDiagnosticService()
    service.tire_pressure_fl = 0.0
    service.tire_pressure_fr = 2.5
    service.tire_pressure_rl = 2.8
    service.tire_pressure_rr = 2.7

    with pytest.raises(ValueError):
        service.GetTireStatus()

def test_get_tire_status_negative_values():
    """
    Verify that GetTireStatus handles negative values gracefully.
    """
    service = TirePressureDiagnosticService()
    service.tire_pressure_fl = -1.0
    service.tire_pressure_fr = 2.5
    service.tire_pressure_rl = 2.8
    service.tire_pressure_rr = 2.7

    with pytest.raises(ValueError):
        service.GetTireStatus()

def test_get_tire_status_overflow_values():
    """
    Verify that GetTireStatus handles overflow values gracefully.
    """
    service = TirePressureDiagnosticService()
    service.tire_pressure_fl = float('inf')
    service.tire_pressure_fr = 2.5
    service.tire_pressure_rl = 2.8
    service.tire_pressure_rr = 2.7

    with pytest.raises(OverflowError):
        service.GetTireStatus()

def test_get_tire_status_race_conditions():
    """
    Verify that GetTireStatus handles race conditions gracefully.
    """
    service = TirePressureDiagnosticService()
    service.tire_pressure_fl = 3.0
    service.tire_pressure_fr = 2.5
    service.tire_pressure_rl = 2.8
    service.tire_pressure_rr = 2.7

    with patch.object(service, 'emit_warning') as mock_emit:
        # Simulate a race condition by changing the tire pressure during the method call
        def change_tire_pressure():
            service.tire_pressure_fl = 1.9

        import threading
        thread = threading.Thread(target=change_tire_pressure)
        thread.start()
        result = service.GetTireStatus()
        thread.join()

    mock_emit.assert_called_once_with(0x0101, 'Low tire pressure')