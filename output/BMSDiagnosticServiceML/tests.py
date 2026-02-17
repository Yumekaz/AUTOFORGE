import pytest
from unittest.mock import Mock, patch

# Mock the ML model inference function
@patch('path_to_module.tire_failure.onnxruntime.InferenceSession')
def test_tire_failure_model(mock_session):
    # Arrange
    mock_session.return_value.run.return_value = [0.1]
    
    tire_pressure_fl = 32
    tire_pressure_fr = 32
    tire_pressure_rl = 32
    tire_pressure_rr = 32
    vehicle_speed_kmh = 50
    ambient_temperature_c = 25
    
    # Act
    result = mock_session.return_value.run.return_value[0]
    
    # Assert
    assert result == 0.1

# Mock the BMSDiagnosticServiceML class
@patch('path_to_module.BMSDiagnosticServiceML')
def test_get_battery_status(mock_service):
    # Arrange
    mock_service.return_value.GetBatteryStatus.return_value = {
        'soc': 25,
        'voltage': 420,
        'current': 10,
        'temperature': 30,
        'health_status': 1
    }
    
    # Act
    result = mock_service.return_value.GetBatteryStatus()
    
    # Assert
    assert result['soc'] == 25
    assert result['voltage'] == 420
    assert result['current'] == 10
    assert result['temperature'] == 30
    assert result['health_status'] == 1

# Mock the BMSDiagnosticServiceML class
@patch('path_to_module.BMSDiagnosticServiceML')
def test_get_estimated_range(mock_service):
    # Arrange
    mock_service.return_value.GetEstimatedRange.return_value = {
        'range_km': 200
    }
    
    driving_mode = 1
    
    # Act
    result = mock_service.return_value.GetEstimatedRange(driving_mode)
    
    # Assert
    assert result['range_km'] == 200

# Mock the BMSDiagnosticServiceML class
@patch('path_to_module.BMSDiagnosticServiceML')
def test_low_battery_warning(mock_service):
    # Arrange
    mock_service.return_value.battery_soc = 15
    
    # Act
    with pytest.raises(Exception) as exc_info:
        mock_service.return_value.check_battery_status()
    
    # Assert
    assert str(exc_info.value) == 'Low battery'

# Mock the BMSDiagnosticServiceML class
@patch('path_to_module.BMSDiagnosticServiceML')
def test_high_temp_warning(mock_service):
    # Arrange
    mock_service.return_value.battery_temperature = 50
    
    # Act
    with pytest.raises(Exception) as exc_info:
        mock_service.return_value.check_battery_status()
    
    # Assert
    assert str(exc_info.value) == 'High temperature'

# Mock the BMSDiagnosticServiceML class
@patch('path_to_module.BMSDiagnosticServiceML')
def test_critical_temp_shutdown(mock_service):
    # Arrange
    mock_service.return_value.battery_temperature = 65
    
    # Act
    with pytest.raises(Exception) as exc_info:
        mock_service.return_value.check_battery_status()
    
    # Assert
    assert str(exc_info.value) == 'Critical temperature - shutdown required'