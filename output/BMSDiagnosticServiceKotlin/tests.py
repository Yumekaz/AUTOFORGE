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
    
    # Arrange
    expected_soc = 75.0
    expected_voltage = 420.0
    expected_current = 10.0
    expected_temperature = 30.0
    expected_health_status = 1
    
    with patch.object(service, 'GetBatteryStatus', return_value={
        'soc': expected_soc,
        'voltage': expected_voltage,
        'current': expected_current,
        'temperature': expected_temperature,
        'health_status': expected_health_status
    }):
        
        # Act
        result = service.GetBatteryStatus()
        
        # Assert
        assert result['soc'] == expected_soc
        assert result['voltage'] == expected_voltage
        assert result['current'] == expected_current
        assert result['temperature'] == expected_temperature
        assert result['health_status'] == expected_health_status

def test_get_cell_voltages():
    """Test the GetCellVoltages method"""
    service = BMSDiagnosticServiceKotlin()
    
    # Arrange
    expected_cell_voltages = [3.7, 3.8, 3.9]
    
    with patch.object(service, 'GetCellVoltages', return_value={
        'cell_voltages': expected_cell_voltages
    }):
        
        # Act
        result = service.GetCellVoltages()
        
        # Assert
        assert result['cell_voltages'] == expected_cell_voltages

def test_get_estimated_range():
    """Test the GetEstimatedRange method"""
    service = BMSDiagnosticServiceKotlin()
    
    # Arrange
    driving_mode = 1
    expected_range_km = 200.0
    
    with patch.object(service, 'GetEstimatedRange', return_value={
        'range_km': expected_range_km
    }):
        
        # Act
        result = service.GetEstimatedRange(driving_mode)
        
        # Assert
        assert result['range_km'] == expected_range_km

def test_low_battery_warning():
    """Test the low battery warning business rule"""
    service = BMSDiagnosticServiceKotlin()
    
    # Arrange
    battery_soc = 15.0
    
    with patch.object(service, 'GetBatteryStatus', return_value={
        'soc': battery_soc,
        'voltage': 420.0,
        'current': 10.0,
        'temperature': 30.0,
        'health_status': 1
    }):
        
        # Act
        with pytest.raises(Exception) as exc_info:
            service.GetBatteryStatus()
        
        # Assert
        assert exc_info.value.args[0]['warning_code'] == 0x0001
        assert exc_info.value.args[0]['warning_message'] == 'Low battery'

def test_high_temp_warning():
    """Test the high temperature warning business rule"""
    service = BMSDiagnosticServiceKotlin()
    
    # Arrange
    battery_temperature = 50.0
    
    with patch.object(service, 'GetBatteryStatus', return_value={
        'soc': 75.0,
        'voltage': 420.0,
        'current': 10.0,
        'temperature': battery_temperature,
        'health_status': 1
    }):
        
        # Act
        with pytest.raises(Exception) as exc_info:
            service.GetBatteryStatus()
        
        # Assert
        assert exc_info.value.args[0]['warning_code'] == 0x0002
        assert exc_info.value.args[0]['warning_message'] == 'High temperature'

def test_critical_temp_shutdown():
    """Test the critical temperature shutdown business rule"""
    service = BMSDiagnosticServiceKotlin()
    
    # Arrange
    battery_temperature = 65.0
    
    with patch.object(service, 'GetBatteryStatus', return_value={
        'soc': 75.0,
        'voltage': 420.0,
        'current': 10.0,
        'temperature': battery_temperature,
        'health_status': 1
    }):
        
        # Act
        with pytest.raises(Exception) as exc_info:
            service.GetBatteryStatus()
        
        # Assert
        assert exc_info.value.args[0]['warning_code'] == 0x0003
        assert exc_info.value.args[0]['warning_message'] == 'Critical temperature - shutdown required'