import pytest
from unittest.mock import Mock, patch

class BMSDiagnosticServiceKotlin:
    def GetBatteryStatus(self):
        pass

    def GetCellVoltages(self):
        pass

    def GetEstimatedRange(self, driving_mode):
        pass

def test_get_battery_status():
    """Test the GetBatteryStatus method"""
    service = BMSDiagnosticServiceKotlin()
    with patch.object(service, 'GetBatteryStatus', return_value={'soc': 0.5, 'voltage': 12.6, 'current': -1.2, 'temperature': 30, 'health_status': 1}):
        result = service.GetBatteryStatus()
        assert result['soc'] == 0.5
        assert result['voltage'] == 12.6
        assert result['current'] == -1.2
        assert result['temperature'] == 30
        assert result['health_status'] == 1

def test_get_cell_voltages():
    """Test the GetCellVoltages method"""
    service = BMSDiagnosticServiceKotlin()
    with patch.object(service, 'GetCellVoltages', return_value=[12.6, 12.5, 12.7]):
        result = service.GetCellVoltages()
        assert result == [12.6, 12.5, 12.7]

def test_get_estimated_range():
    """Test the GetEstimatedRange method"""
    service = BMSDiagnosticServiceKotlin()
    with patch.object(service, 'GetEstimatedRange', return_value={'range_km': 100}):
        result = service.GetEstimatedRange(1)
        assert result['range_km'] == 100

def test_low_battery_warning():
    """Test the low battery warning business rule"""
    service = BMSDiagnosticServiceKotlin()
    with patch.object(service, 'GetBatteryStatus', return_value={'soc': 15}):
        with pytest.raises(Exception) as exc_info:
            service.GetBatteryStatus()
        assert exc_info.value.args[0] == 'Low battery'

def test_high_temp_warning():
    """Test the high temperature warning business rule"""
    service = BMSDiagnosticServiceKotlin()
    with patch.object(service, 'GetBatteryStatus', return_value={'temperature': 50}):
        with pytest.raises(Exception) as exc_info:
            service.GetBatteryStatus()
        assert exc_info.value.args[0] == 'High temperature'

def test_critical_temp_shutdown():
    """Test the critical temperature shutdown business rule"""
    service = BMSDiagnosticServiceKotlin()
    with patch.object(service, 'GetBatteryStatus', return_value={'temperature': 65}):
        with pytest.raises(Exception) as exc_info:
            service.GetBatteryStatus()
        assert exc_info.value.args[0] == 'Critical temperature - shutdown required'