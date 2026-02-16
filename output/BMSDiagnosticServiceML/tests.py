import pytest
from unittest.mock import patch, Mock

# Assuming the service implementation is in a module named 'bms_service'
from bms_service import BMSDiagnosticServiceML

@pytest.fixture
def bms_service():
    return BMSDiagnosticServiceML()

@patch('bms_service.onnxruntime.InferenceSession')
def test_get_battery_status(mock_session, bms_service):
    """
    Test the GetBatteryStatus method with normal battery parameters.
    """
    mock_session.return_value.run.return_value = [0.85, 420.0, -10.0, 30]
    
    result = bms_service.GetBatteryStatus()
    
    assert result == {
        'soc': 0.85,
        'voltage': 420.0,
        'current': -10.0,
        'temperature': 30,
        'health_status': 0
    }

@patch('bms_service.onnxruntime.InferenceSession')
def test_get_battery_status_low_soc(mock_session, bms_service):
    """
    Test the GetBatteryStatus method with low battery state.
    """
    mock_session.return_value.run.return_value = [19.5, 420.0, -10.0, 30]
    
    result = bms_service.GetBatteryStatus()
    
    assert result == {
        'soc': 19.5,
        'voltage': 420.0,
        'current': -10.0,
        'temperature': 30,
        'health_status': 0
    }

@patch('bms_service.onnxruntime.InferenceSession')
def test_get_battery_status_high_temperature(mock_session, bms_service):
    """
    Test the GetBatteryStatus method with high temperature state.
    """
    mock_session.return_value.run.return_value = [0.85, 420.0, -10.0, 46]
    
    result = bms_service.GetBatteryStatus()
    
    assert result == {
        'soc': 0.85,
        'voltage': 420.0,
        'current': -10.0,
        'temperature': 46,
        'health_status': 0
    }

@patch('bms_service.onnxruntime.InferenceSession')
def test_get_battery_status_critical_temperature(mock_session, bms_service):
    """
    Test the GetBatteryStatus method with critical temperature state.
    """
    mock_session.return_value.run.return_value = [0.85, 420.0, -10.0, 61]
    
    result = bms_service.GetBatteryStatus()
    
    assert result == {
        'soc': 0.85,
        'voltage': 420.0,
        'current': -10.0,
        'temperature': 61,
        'health_status': 0
    }

@patch('bms_service.onnxruntime.InferenceSession')
def test_get_estimated_range(mock_session, bms_service):
    """
    Test the GetEstimatedRange method with normal driving mode.
    """
    mock_session.return_value.run.return_value = [0.85, 420.0, -10.0, 30]
    
    result = bms_service.GetEstimatedRange(1)
    
    assert result == {
        'range_km': 100.0
    }

@patch('bms_service.onnxruntime.InferenceSession')
def test_get_estimated_range_invalid_driving_mode(mock_session, bms_service):
    """
    Test the GetEstimatedRange method with invalid driving mode.
    """
    mock_session.return_value.run.return_value = [0.85, 420.0, -10.0, 30]
    
    result = bms_service.GetEstimatedRange(255)
    
    assert result == {
        'range_km': 0.0
    }