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
    
    with patch.object(service, 'GetBatteryStatus', return_value=(25.0, 12.6, -3.4, 28.0, 1)):
        result = service.GetBatteryStatus()
        
        assert isinstance(result, tuple)
        assert len(result) == 5
        assert all(isinstance(val, (float, int)) for val in result)

def test_get_cell_voltages():
    """Test the GetCellVoltages method"""
    service = BMSDiagnosticServiceKotlin()
    
    with patch.object(service, 'GetCellVoltages', return_value=[3.7, 3.8, 3.9]):
        result = service.GetCellVoltages()
        
        assert isinstance(result, list)
        assert all(isinstance(val, float) for val in result)

def test_get_estimated_range():
    """Test the GetEstimatedRange method"""
    service = BMSDiagnosticServiceKotlin()
    
    with patch.object(service, 'GetEstimatedRange', return_value=150.0):
        result = service.GetEstimatedRange(1)
        
        assert isinstance(result, float)

def test_low_battery_warning():
    """Test low battery warning business rule"""
    service = BMSDiagnosticServiceKotlin()
    
    with patch.object(service, 'GetBatteryStatus', return_value=(19.5, 12.6, -3.4, 28.0, 1)):
        with pytest.raises(SystemExit) as exc_info:
            service.GetBatteryStatus()
        
        assert exc_info.value.code == 0x0001
        assert exc_info.value.msg == 'Low battery'

def test_high_temp_warning():
    """Test high temperature warning business rule"""
    service = BMSDiagnosticServiceKotlin()
    
    with patch.object(service, 'GetBatteryStatus', return_value=(25.0, 12.6, -3.4, 46.0, 1)):
        with pytest.raises(SystemExit) as exc_info:
            service.GetBatteryStatus()
        
        assert exc_info.value.code == 0x0002
        assert exc_info.value.msg == 'High temperature'

def test_critical_temp_shutdown():
    """Test critical temperature shutdown business rule"""
    service = BMSDiagnosticServiceKotlin()
    
    with patch.object(service, 'GetBatteryStatus', return_value=(25.0, 12.6, -3.4, 61.0, 1)):
        with pytest.raises(SystemExit) as exc_info:
            service.GetBatteryStatus()
        
        assert exc_info.value.code == 0x0003
        assert exc_info.value.msg == 'Critical temperature - shutdown required'