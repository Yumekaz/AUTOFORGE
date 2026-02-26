import pytest
from unittest.mock import Mock, patch

class BatteryManagementSystem:
    def __init__(self):
        self.battery_soc = 0.0
        self.battery_voltage = 0.0
        self.battery_current = 0.0
        self.battery_temperature = 0.0
        self.warnings = []

    def GetBatteryStatus(self):
        return {
            "soc": self.battery_soc,
            "voltage": self.battery_voltage,
            "current": self.battery_current,
            "temperature": self.battery_temperature,
            "health_status": self._get_health_status()
        }

    def _get_health_status(self):
        if self.battery_soc < 20:
            return 1
        elif self.battery_temperature > 45:
            return 1
        elif self.battery_temperature > 60:
            return 2
        else:
            return 0

    def GetCellVoltages(self):
        return []

    def GetEstimatedRange(self, driving_mode):
        return 0.0

def test_get_battery_status():
    """Test the GetBatteryStatus method with normal values."""
    bms = BatteryManagementSystem()
    bms.battery_soc = 50
    bms.battery_voltage = 420
    bms.battery_current = 10
    bms.battery_temperature = 30

    result = bms.GetBatteryStatus()

    assert result["soc"] == 50.0
    assert result["voltage"] == 420.0
    assert result["current"] == 10.0
    assert result["temperature"] == 30.0
    assert result["health_status"] == 0

def test_get_battery_status_low_soc():
    """Test the GetBatteryStatus method with low battery SOC."""
    bms = BatteryManagementSystem()
    bms.battery_soc = 15
    bms.battery_voltage = 420
    bms.battery_current = 10
    bms.battery_temperature = 30

    result = bms.GetBatteryStatus()

    assert result["soc"] == 15.0
    assert result["voltage"] == 420.0
    assert result["current"] == 10.0
    assert result["temperature"] == 30.0
    assert result["health_status"] == 1

def test_get_battery_status_high_temp():
    """Test the GetBatteryStatus method with high battery temperature."""
    bms = BatteryManagementSystem()
    bms.battery_soc = 50
    bms.battery_voltage = 420
    bms.battery_current = 10
    bms.battery_temperature = 46

    result = bms.GetBatteryStatus()

    assert result["soc"] == 50.0
    assert result["voltage"] == 420.0
    assert result["current"] == 10.0
    assert result["temperature"] == 46.0
    assert result["health_status"] == 1

def test_get_battery_status_critical_temp():
    """Test the GetBatteryStatus method with critical battery temperature."""
    bms = BatteryManagementSystem()
    bms.battery_soc = 50
    bms.battery_voltage = 420
    bms.battery_current = 10
    bms.battery_temperature = 61

    result = bms.GetBatteryStatus()

    assert result["soc"] == 50.0
    assert result["voltage"] == 420.0
    assert result["current"] == 10.0
    assert result["temperature"] == 61.0
    assert result["health_status"] == 2

def test_get_cell_voltages():
    """Test the GetCellVoltages method."""
    bms = BatteryManagementSystem()

    result = bms.GetCellVoltages()

    assert result == []

def test_get_estimated_range_eco_mode():
    """Test the GetEstimatedRange method with ECO mode."""
    bms = BatteryManagementSystem()

    result = bms.GetEstimatedRange(0)

    assert result == 0.0

def test_get_estimated_range_normal_mode():
    """Test the GetEstimatedRange method with NORMAL mode."""
    bms = BatteryManagementSystem()

    result = bms.GetEstimatedRange(1)

    assert result == 0.0

def test_get_estimated_range_sport_mode():
    """Test the GetEstimatedRange method with SPORT mode."""
    bms = BatteryManagementSystem()

    result = bms.GetEstimatedRange(2)

    assert result == 0.0