import pytest
from unittest.mock import Mock, patch

# Mock the SOME/IP client to simulate service calls
class MockSOMEIPClient:
    def __init__(self):
        self.methods = {
            1: self.GetBatteryStatus,
            2: self.GetCellVoltages,
            3: self.GetEstimatedRange
        }

    def GetBatteryStatus(self, *args, **kwargs):
        return {
            'soc': 50.0,
            'voltage': 420.0,
            'current': 10.0,
            'temperature': 30.0,
            'health_status': 0
        }

    def GetCellVoltages(self, *args, **kwargs):
        return {
            'cell_voltages': [3.7, 3.8, 3.9]
        }

    def GetEstimatedRange(self, driving_mode=1, *args, **kwargs):
        if driving_mode == 0:
            return {'range_km': 200.0}
        elif driving_mode == 1:
            return {'range_km': 400.0}
        elif driving_mode == 2:
            return {'range_km': 600.0}

    def emit(self, event_name, *args, **kwargs):
        pass

@pytest.fixture
def mock_client():
    return MockSOMEIPClient()

def test_GetBatteryStatus(mock_client):
    """
    Test the GetBatteryStatus method with normal values.
    """
    result = mock_client.methods[1]()
    assert result['soc'] == 50.0
    assert result['voltage'] == 420.0
    assert result['current'] == 10.0
    assert result['temperature'] == 30.0
    assert result['health_status'] == 0

def test_GetBatteryStatus_low_soc(mock_client):
    """
    Test the GetBatteryStatus method with low SOC.
    """
    mock_client.methods[1] = Mock(return_value={'soc': 15.0, 'voltage': 420.0, 'current': 10.0, 'temperature': 30.0, 'health_status': 0})
    result = mock_client.methods[1]()
    assert result['soc'] == 15.0
    assert result['health_status'] == 1

def test_GetBatteryStatus_high_temperature(mock_client):
    """
    Test the GetBatteryStatus method with high temperature.
    """
    mock_client.methods[1] = Mock(return_value={'soc': 50.0, 'voltage': 420.0, 'current': 10.0, 'temperature': 46.0, 'health_status': 0})
    result = mock_client.methods[1]()
    assert result['temperature'] == 46.0
    assert result['health_status'] == 1

def test_GetBatteryStatus_critical_temperature(mock_client):
    """
    Test the GetBatteryStatus method with critical temperature.
    """
    mock_client.methods[1] = Mock(return_value={'soc': 50.0, 'voltage': 420.0, 'current': 10.0, 'temperature': 61.0, 'health_status': 0})
    result = mock_client.methods[1]()
    assert result['temperature'] == 61.0
    assert result['health_status'] == 2

def test_GetCellVoltages(mock_client):
    """
    Test the GetCellVoltages method with normal values.
    """
    result = mock_client.methods[2]()
    assert result['cell_voltages'] == [3.7, 3.8, 3.9]

def test_GetEstimatedRange_eco_mode(mock_client):
    """
    Test the GetEstimatedRange method in ECO mode.
    """
    result = mock_client.methods[3](0)
    assert result['range_km'] == 200.0

def test_GetEstimatedRange_normal_mode(mock_client):
    """
    Test the GetEstimatedRange method in NORMAL mode.
    """
    result = mock_client.methods[3](1)
    assert result['range_km'] == 400.0

def test_GetEstimatedRange_sport_mode(mock_client):
    """
    Test the GetEstimatedRange method in SPORT mode.
    """
    result = mock_client.methods[3](2)
    assert result['range_km'] == 600.0