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
    
    # Arrange
    expected_output = {
        'soc': 0.5,
        'voltage': 12.6,
        'current': -3.4,
        'temperature': 28.0,
        'health_status': 1
    }
    
    bms_service.GetBatteryStatus = Mock(return_value=expected_output)
    
    # Act
    result = bms_service.GetBatteryStatus()
    
    # Assert
    assert result == expected_output

def test_get_cell_voltages():
    """Test the GetCellVoltages method"""
    bms_service = BMSDiagnosticServiceJava()
    
    # Arrange
    expected_output = [3.7, 3.8, 3.9, 4.0]
    
    bms_service.GetCellVoltages = Mock(return_value=expected_output)
    
    # Act
    result = bms_service.GetCellVoltages()
    
    # Assert
    assert result == expected_output

def test_get_estimated_range():
    """Test the GetEstimatedRange method"""
    bms_service = BMSDiagnosticServiceJava()
    
    # Arrange
    driving_mode = 1
    expected_output = 200.5
    
    bms_service.GetEstimatedRange = Mock(return_value=expected_output)
    
    # Act
    result = bms_service.GetEstimatedRange(driving_mode)
    
    # Assert
    assert result == expected_output

def test_low_battery_warning():
    """Test the low battery warning business rule"""
    with patch('BMSDiagnosticServiceJava.BatteryWarning') as mock_warning:
        bms_service = BMSDiagnosticServiceJava()
        
        # Arrange
        battery_soc = 15
        
        # Act
        bms_service.GetBatteryStatus()
        
        # Assert
        mock_warning.assert_called_once_with(code=0x0001, msg='Low battery')

def test_high_temp_warning():
    """Test the high temperature warning business rule"""
    with patch('BMSDiagnosticServiceJava.BatteryWarning') as mock_warning:
        bms_service = BMSDiagnosticServiceJava()
        
        # Arrange
        battery_temperature = 50
        
        # Act
        bms_service.GetBatteryStatus()
        
        # Assert
        mock_warning.assert_called_once_with(code=0x0002, msg='High temperature')

def test_critical_temp_shutdown():
    """Test the critical temperature shutdown business rule"""
    with patch('BMSDiagnosticServiceJava.BatteryWarning') as mock_warning:
        bms_service = BMSDiagnosticServiceJava()
        
        # Arrange
        battery_temperature = 65
        
        # Act
        bms_service.GetBatteryStatus()
        
        # Assert
        mock_warning.assert_called_once_with(code=0x0003, msg='Critical temperature - shutdown required')