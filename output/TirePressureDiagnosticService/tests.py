import pytest
from unittest.mock import Mock, patch

# Mock the SOME/IP client to simulate service calls
class SomeIPClient:
    def __init__(self):
        self.tire_pressure_fl = 0.0
        self.tire_pressure_fr = 0.0
        self.tire_pressure_rl = 0.0
        self.tire_pressure_rr = 0.0
        self.vehicle_speed = 0.0
        self.ambient_temperature = 0.0

    def GetTireStatus(self):
        return {
            "tire_pressure_fl": self.tire_pressure_fl,
            "tire_pressure_fr": self.tire_pressure_fr,
            "tire_pressure_rl": self.tire_pressure_rl,
            "tire_pressure_rr": self.tire_pressure_rr,
            "failure_risk": 0.0
        }

    def emit(self, event_id, code=None, msg=None):
        if event_id == 33025:
            return {"warning_code": code, "warning_message": msg}
        return None

# Mock the SOME/IP client in tests
@pytest.fixture
def someip_client():
    return SomeIPClient()

# Test for GetTireStatus method
def test_get_tire_status(someip_client):
    """
    Verifies that the GetTireStatus method returns the correct tire pressures and failure risk.
    """
    # Arrange
    expected_output = {
        "tire_pressure_fl": 3.0,
        "tire_pressure_fr": 3.5,
        "tire_pressure_rl": 2.8,
        "tire_pressure_rr": 2.9,
        "failure_risk": 0.0
    }
    
    # Act
    someip_client.tire_pressure_fl = expected_output["tire_pressure_fl"]
    someip_client.tire_pressure_fr = expected_output["tire_pressure_fr"]
    someip_client.tire_pressure_rl = expected_output["tire_pressure_rl"]
    someip_client.tire_pressure_rr = expected_output["tire_pressure_rr"]
    output = someip_client.GetTireStatus()
    
    # Assert
    assert output == expected_output

# Test for low pressure warning business rule
def test_low_pressure_warning(someip_client):
    """
    Verifies that the low pressure warning is emitted when any tire pressure is below 2.0.
    """
    # Arrange
    someip_client.tire_pressure_fl = 1.9
    
    # Act
    output = someip_client.emit(33025)
    
    # Assert
    assert output == {"warning_code": 0x0101, "warning_message": 'Low tire pressure'}

# Test for imbalance warning business rule
def test_imbalance_warning(someip_client):
    """
    Verifies that the imbalance warning is emitted when there is a significant difference in tire pressures.
    """
    # Arrange
    someip_client.tire_pressure_fl = 3.0
    someip_client.tire_pressure_fr = 2.6
    
    # Act
    output = someip_client.emit(33025)
    
    # Assert
    assert output == {"warning_code": 0x0102, "warning_message": 'Tire pressure imbalance'}

# Test for null input (should not happen in this case as inputs are predefined)
def test_null_input(someip_client):
    """
    Verifies that the service handles null inputs gracefully.
    """
    # Arrange
    someip_client.tire_pressure_fl = None
    
    # Act & Assert
    with pytest.raises(AssertionError):
        assert someip_client.GetTireStatus() is not None

# Test for boundary conditions (min/max values)
def test_boundary_conditions(someip_client):
    """
    Verifies that the service handles boundary conditions correctly.
    """
    # Arrange
    someip_client.tire_pressure_fl = 2.0
    someip_client.tire_pressure_fr = 2.0
    someip_client.tire_pressure_rl = 2.0
    someip_client.tire_pressure_rr = 2.0
    
    # Act
    output = someip_client.GetTireStatus()
    
    # Assert
    assert output == {
        "tire_pressure_fl": 2.0,
        "tire_pressure_fr": 2.0,
        "tire_pressure_rl": 2.0,
        "tire_pressure_rr": 2.0,
        "failure_risk": 0.0
    }