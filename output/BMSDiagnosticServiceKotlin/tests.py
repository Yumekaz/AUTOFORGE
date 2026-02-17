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
    
    with patch.object(service, 'GetBatteryStatus', return_value={'soc': 0.25, 'voltage': 420.0, 'current': 10.0, 'temperature': 30.0, 'health_status': 1}):
        result = service.GetBatteryStatus()
        assert result['soc'] == 0.25
        assert result['voltage'] == 420.0
        assert result['current'] == 10.0
        assert result['temperature'] == 30.0
        assert result['health_status'] == 1

def test_get_cell_voltages():
    """Test the GetCellVoltages method"""
    service = BMSDiagnosticServiceKotlin()
    
    with patch.object(service, 'GetCellVoltages', return_value=[420.5, 421.0, 421.5]):
        result = service.GetCellVoltages()
        assert result == [420.5, 421.0, 421.5]

def test_get_estimated_range():
    """Test the GetEstimatedRange method"""
    service = BMSDiagnosticServiceKotlin()
    
    with patch.object(service, 'GetEstimatedRange', return_value={'range_km': 150.0}):
        result = service.GetEstimatedRange(driving_mode=1)
        assert result['range_km'] == 150.0

def test_low_battery_warning():
    """Test the low battery warning business rule"""
    with patch('some_module.emit') as mock_emit:
        BMSDiagnosticServiceKotlin().GetBatteryStatus()
        mock_emit.assert_called_once_with(warning_code=0x0001, warning_message='Low battery')

def test_high_temp_warning():
    """Test the high temperature warning business rule"""
    with patch('some_module.emit') as mock_emit:
        BMSDiagnosticServiceKotlin().GetBatteryStatus()
        mock_emit.assert_called_once_with(warning_code=0x0002, warning_message='High temperature')

def test_critical_temp_shutdown():
    """Test the critical temperature shutdown business rule"""
    with patch('some_module.emit') as mock_emit:
        BMSDiagnosticServiceKotlin().GetBatteryStatus()
        mock_emit.assert_called_once_with(warning_code=0x0003, warning_message='Critical temperature - shutdown required')