
import pytest

def test_get_battery_status():
    """Test GetBatteryStatus returns valid data."""
    service = BMSDiagnosticService()
    status = service.get_battery_status()
    
    assert 0 <= status.soc <= 100
    assert status.voltage > 0
    assert status.health_status in [0, 1, 2]

def test_low_battery_warning():
    """Test warning emitted when SOC < 20%."""
    service = BMSDiagnosticService()
    service.set_battery_soc(15)
    
    warnings = service.get_warnings()
    assert any(w.code == 0x0001 for w in warnings)
