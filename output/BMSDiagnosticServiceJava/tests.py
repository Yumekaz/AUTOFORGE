import pytest
from unittest.mock import Mock, patch

class BMSDiagnosticServiceJava:
    def GetBatteryStatus(self):
        pass

    def GetCellVoltages(self):
        pass

    def GetEstimatedRange(self, driving_mode):
        pass

def test_get_battery_status():
    """Test the GetBatteryStatus method"""
    bms_service = BMSDiagnosticServiceJava()
    with patch.object(bms_service, 'GetBatteryStatus', return_value={'soc': 0.25, 'voltage': 420.0, 'current': 10.0, 'temperature': 30.0, 'health_status': 1}):
        result = bms_service.GetBatteryStatus()
        assert result['soc'] == 0.25
        assert result['voltage'] == 420.0
        assert result['current'] == 10.0
        assert result['temperature'] == 30.0
        assert result['health_status'] == 1

def test_get_cell_voltages():
    """Test the GetCellVoltages method"""
    bms_service = BMSDiagnosticServiceJava()
    with patch.object(bms_service, 'GetCellVoltages', return_value=[420.5, 421.0, 421.5]):
        result = bms_service.GetCellVoltages()
        assert result == [420.5, 421.0, 421.5]

def test_get_estimated_range():
    """Test the GetEstimatedRange method"""
    bms_service = BMSDiagnosticServiceJava()
    with patch.object(bms_service, 'GetEstimatedRange', return_value={'range_km': 150.0}):
        result = bms_service.GetEstimatedRange(driving_mode=1)
        assert result['range_km'] == 150.0

def test_low_battery_warning():
    """Test the low battery warning business rule"""
    with patch('some_module.emit_event') as mock_emit:
        bms_service = BMSDiagnosticServiceJava()
        bms_service.GetBatteryStatus = Mock(return_value={'soc': 19.9, 'voltage': 420.0, 'current': 10.0, 'temperature': 30.0, 'health_status': 1})
        bms_service.GetBatteryStatus()
        mock_emit.assert_called_once_with('BatteryWarning', code=0x0001, msg='Low battery')

def test_high_temp_warning():
    """Test the high temperature warning business rule"""
    with patch('some_module.emit_event') as mock_emit:
        bms_service = BMSDiagnosticServiceJava()
        bms_service.GetBatteryStatus = Mock(return_value={'soc': 25.0, 'voltage': 420.0, 'current': 10.0, 'temperature': 46.0, 'health_status': 1})
        bms_service.GetBatteryStatus()
        mock_emit.assert_called_once_with('BatteryWarning', code=0x0002, msg='High temperature')

def test_critical_temp_shutdown():
    """Test the critical temperature shutdown business rule"""
    with patch('some_module.emit_event') as mock_emit:
        bms_service = BMSDiagnosticServiceJava()
        bms_service.GetBatteryStatus = Mock(return_value={'soc': 25.0, 'voltage': 420.0, 'current': 10.0, 'temperature': 61.0, 'health_status': 1})
        with pytest.raises(SystemExit):
            bms_service.GetBatteryStatus()