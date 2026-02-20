import pytest
from unittest.mock import Mock, patch

# Mock the SOME/IP service implementation
class MotorHealthDiagnosticService:
    def GetMotorHealth(self):
        return {
            'motor_temperature': 0.0,
            'motor_torque': 0.0,
            'motor_power': 0.0,
            'health_status': 0
        }

    def emit_MotorWarning(self, code, msg):
        pass

# Test cases for MotorHealthDiagnosticService

def test_get_motor_health():
    """
    Test the GetMotorHealth method with normal values.
    """
    service = MotorHealthDiagnosticService()
    result = service.GetMotorHealth()
    assert isinstance(result['motor_temperature'], float)
    assert isinstance(result['motor_torque'], float)
    assert isinstance(result['motor_power'], float)
    assert isinstance(result['health_status'], int)

def test_get_motor_health_edge_cases():
    """
    Test the GetMotorHealth method with edge cases.
    """
    service = MotorHealthDiagnosticService()
    
    # Test with very high temperature
    with patch.object(service, 'emit_MotorWarning') as mock_warning:
        result = service.GetMotorHealth(motor_temperature=105)
        assert mock_warning.call_args_list == [((0x0202, 'Motor critical temperature'),)]
    
    # Test with high temperature but not critical
    with patch.object(service, 'emit_MotorWarning') as mock_warning:
        result = service.GetMotorHealth(motor_temperature=90)
        assert mock_warning.call_args_list == [((0x0201, 'Motor temperature high'),)]

def test_get_motor_health_error_conditions():
    """
    Test the GetMotorHealth method with error conditions.
    """
    service = MotorHealthDiagnosticService()
    
    # Test with negative temperature
    with pytest.raises(ValueError):
        result = service.GetMotorHealth(motor_temperature=-5)
    
    # Test with non-numeric values
    with pytest.raises(TypeError):
        result = service.GetMotorHealth(motor_temperature='100')

def test_motor_health_business_rules():
    """
    Test the business rules defined in the requirement.
    """
    service = MotorHealthDiagnosticService()
    
    # Test high temperature warning
    with patch.object(service, 'emit_MotorWarning') as mock_warning:
        result = service.GetMotorHealth(motor_temperature=86)
        assert mock_warning.call_args_list == [((0x0201, 'Motor temperature high'),)]
    
    # Test critical temperature warning
    with patch.object(service, 'emit_MotorWarning') as mock_warning:
        result = service.GetMotorHealth(motor_temperature=101)
        assert mock_warning.call_args_list == [((0x0202, 'Motor critical temperature'),)]

def test_motor_health_event_emission():
    """
    Test the event emission logic.
    """
    service = MotorHealthDiagnosticService()
    
    # Test high temperature warning
    with patch.object(service, 'emit_MotorWarning') as mock_warning:
        result = service.GetMotorHealth(motor_temperature=86)
        assert mock_warning.call_args_list == [((0x0201, 'Motor temperature high'),)]
    
    # Test critical temperature warning
    with patch.object(service, 'emit_MotorWarning') as mock_warning:
        result = service.GetMotorHealth(motor_temperature=101)
        assert mock_warning.call_args_list == [((0x0202, 'Motor critical temperature'),)]

def test_motor_health_invalid_input():
    """
    Test the handling of invalid input.
    """
    service = MotorHealthDiagnosticService()
    
    # Test with None input
    with pytest.raises(TypeError):
        result = service.GetMotorHealth(motor_temperature=None)
    
    # Test with empty string input
    with pytest.raises(ValueError):
        result = service.GetMotorHealth(motor_temperature='')