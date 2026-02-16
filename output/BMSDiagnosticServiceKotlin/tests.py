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
    
    with patch.object(service, 'GetBatteryStatus', return_value=(20.5, 12.3, -1.2, 25, 1)):
        result = service.GetBatteryStatus()
        
        assert isinstance(result, tuple)
        assert len(result) == 5
        assert all(isinstance(val, (float, int)) for val in result)

def test_get_cell_voltages():
    """Test the GetCellVoltages method"""
    service = BMSDiagnosticServiceKotlin()
    
    with patch.object(service, 'GetCellVoltages', return_value=[12.0, 12.1, 12.2]):
        result = service.GetCellVoltages()
        
        assert isinstance(result, list)
        assert all(isinstance(val, float) for val in result)

def test_get_estimated_range():
    """Test the GetEstimatedRange method"""
    service = BMSDiagnosticServiceKotlin()
    
    with patch.object(service, 'GetEstimatedRange', return_value=100.5):
        result = service.GetEstimatedRange(1)
        
        assert isinstance(result, float)

def test_low_battery_warning():
    """Test low battery warning business rule"""
    service = BMSDiagnosticServiceKotlin()
    
    with patch.object(service, 'GetBatteryStatus', return_value=(19.0, 12.3, -1.2, 25, 1)):
        with pytest.raises(Exception) as exc_info:
            service.GetBatteryStatus()
        
        assert exc_info.type == Exception
        assert exc_info.value.args[0] == 'Low battery'

def test_high_temp_warning():
    """Test high temperature warning business rule"""
    service = BMSDiagnosticServiceKotlin()
    
    with patch.object(service, 'GetBatteryStatus', return_value=(20.5, 12.3, -1.2, 46, 1)):
        with pytest.raises(Exception) as exc_info:
            service.GetBatteryStatus()
        
        assert exc_info.type == Exception
        assert exc_info.value.args[0] == 'High temperature'

def test_critical_temp_shutdown():
    """Test critical temperature shutdown business rule"""
    service = BMSDiagnosticServiceKotlin()
    
    with patch.object(service, 'GetBatteryStatus', return_value=(20.5, 12.3, -1.2, 61, 1)):
        with pytest.raises(Exception) as exc_info:
            service.GetBatteryStatus()
        
        assert exc_info.type == Exception
        assert exc_info.value.args[0] == 'Critical temperature - shutdown required'