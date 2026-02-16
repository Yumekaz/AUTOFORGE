import pytest
from unittest.mock import Mock, patch

# Mock the SOME/IP client to simulate service calls
class MockSOMEIPClient:
    def __init__(self):
        self.methods = {
            1: self.get_battery_status,
            2: self.get_cell_voltages,
            3: self.get_estimated_range
        }
    
    def get_method(self, method_id):
        return self.methods[method_id]
    
    def get_battery_status(self):
        return (0.5, 420.0, 10.0, 25.0, 1)
    
    def get_cell_voltages(self):
        return [3.7, 3.8, 3.9, 4.0]
    
    def get_estimated_range(self, driving_mode):
        if driving_mode == 1:
            return 200.0
        else:
            return 150.0

# Mock the BatteryWarning event emitter
class MockBatteryWarningEmitter:
    def __init__(self):
        self.warnings = []
    
    def emit(self, warning_code, warning_message):
        self.warnings.append((warning_code, warning_message))

@pytest.fixture
def mock_client():
    return MockSOMEIPClient()

@pytest.fixture
def mock_emitter():
    return MockBatteryWarningEmitter()

# Test the GetBatteryStatus method
def test_get_battery_status(mock_client, mock_emitter):
    # Arrange
    bms_service = BMSDiagnosticServiceJava(mock_client, mock_emitter)
    
    # Act
    soc, voltage, current, temperature, health_status = bms_service.GetBatteryStatus()
    
    # Assert
    assert soc == 0.5
    assert voltage == 420.0
    assert current == 10.0
    assert temperature == 25.0
    assert health_status == 1

# Test the GetCellVoltages method
def test_get_cell_voltages(mock_client, mock_emitter):
    # Arrange
    bms_service = BMSDiagnosticServiceJava(mock_client, mock_emitter)
    
    # Act
    cell_voltages = bms_service.GetCellVoltages()
    
    # Assert
    assert cell_voltages == [3.7, 3.8, 3.9, 4.0]

# Test the GetEstimatedRange method with valid driving mode
def test_get_estimated_range_valid_mode(mock_client, mock_emitter):
    # Arrange
    bms_service = BMSDiagnosticServiceJava(mock_client, mock_emitter)
    
    # Act
    range_km = bms_service.GetEstimatedRange(1)
    
    # Assert
    assert range_km == 200.0

# Test the GetEstimatedRange method with invalid driving mode
def test_get_estimated_range_invalid_mode(mock_client, mock_emitter):
    # Arrange
    bms_service = BMSDiagnosticServiceJava(mock_client, mock_emitter)
    
    # Act
    range_km = bms_service.GetEstimatedRange(2)
    
    # Assert
    assert range_km == 150.0

# Test the low battery warning condition
def test_low_battery_warning(mock_client, mock_emitter):
    # Arrange
    mock_client.get_battery_status.return_value = (19.0, 420.0, 10.0, 25.0, 1)
    bms_service = BMSDiagnosticServiceJava(mock_client, mock_emitter)
    
    # Act
    bms_service.GetBatteryStatus()
    
    # Assert
    assert mock_emitter.warnings == [(0x0001, 'Low battery')]

# Test the high temperature warning condition
def test_high_temperature_warning(mock_client, mock_emitter):
    # Arrange
    mock_client.get_battery_status.return_value = (50.0, 420.0, 10.0, 46.0, 1)
    bms_service = BMSDiagnosticServiceJava(mock_client, mock_emitter)
    
    # Act
    bms_service.GetBatteryStatus()
    
    # Assert
    assert mock_emitter.warnings == [(0x0002, 'High temperature')]

# Test the critical temperature shutdown condition
def test_critical_temperature_shutdown(mock_client, mock_emitter):
    # Arrange
    mock_client.get_battery_status.return_value = (50.0, 420.0, 10.0, 61.0, 1)
    bms_service = BMSDiagnosticServiceJava(mock_client, mock_emitter)
    
    # Act
    with pytest.raises(SystemExit):
        bms_service.GetBatteryStatus()
    
    # Assert
    assert mock_emitter.warnings == [(0x0003, 'Critical temperature - shutdown required')]