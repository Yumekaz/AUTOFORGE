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
    
    with patch.object(bms_service, 'GetBatteryStatus', return_value={'soc': 25.0, 'voltage': 420.0, 'current': 10.0, 'temperature': 30.0, 'health_status': 1}):
        result = bms_service.GetBatteryStatus()
        assert result['soc'] == 25.0
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
    bms_service = BMSDiagnosticServiceJava()
    
    with patch.object(bms_service, 'GetBatteryStatus', return_value={'soc': 19.0, 'voltage': 420.0, 'current': 10.0, 'temperature': 30.0, 'health_status': 1}):
        with pytest.raises(Exception) as e:
            bms_service.GetBatteryStatus()
        assert str(e.value) == 'Low battery'

def test_high_temp_warning():
    """Test the high temperature warning business rule"""
    bms_service = BMSDiagnosticServiceJava()
    
    with patch.object(bms_service, 'GetBatteryStatus', return_value={'soc': 25.0, 'voltage': 420.0, 'current': 10.0, 'temperature': 46.0, 'health_status': 1}):
        with pytest.raises(Exception) as e:
            bms_service.GetBatteryStatus()
        assert str(e.value) == 'High temperature'

def test_critical_temp_shutdown():
    """Test the critical temperature shutdown business rule"""
    bms_service = BMSDiagnosticServiceJava()
    
    with patch.object(bms_service, 'GetBatteryStatus', return_value={'soc': 25.0, 'voltage': 420.0, 'current': 10.0, 'temperature': 61.0, 'health_status': 1}):
        with pytest.raises(Exception) as e:
            bms_service.GetBatteryStatus()
        assert str(e.value) == 'Critical temperature - shutdown required'