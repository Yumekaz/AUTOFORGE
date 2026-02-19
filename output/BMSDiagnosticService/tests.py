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
            'cell_voltages': [3.7] * 8
        }
    
    def GetEstimatedRange(self, driving_mode=1, *args, **kwargs):
        if driving_mode == 0:
            return {'range_km': 200.0}
        elif driving_mode == 1:
            return {'range_km': 300.0}
        elif driving_mode == 2:
            return {'range_km': 400.0}

# Mock the SOME/IP client instance
mock_client = MockSOMEIPClient()

@patch('your_module.SOMEIPClient', return_value=mock_client)
def test_GetBatteryStatus(mock_someip_client):
    """
    Test the GetBatteryStatus method with normal values.
    """
    response = mock_client.methods[1]()
    assert response['soc'] == 50.0
    assert response['voltage'] == 420.0
    assert response['current'] == 10.0
    assert response['temperature'] == 30.0
    assert response['health_status'] == 0

@patch('your_module.SOMEIPClient', return_value=mock_client)
def test_GetBatteryStatus_low_soc(mock_someip_client):
    """
    Test the GetBatteryStatus method with low SOC.
    """
    mock_client.methods[1] = Mock(return_value={'soc': 15.0, 'voltage': 420.0, 'current': 10.0, 'temperature': 30.0, 'health_status': 0})
    response = mock_client.methods[1]()
    assert response['soc'] == 15.0
    assert response['voltage'] == 420.0
    assert response['current'] == 10.0
    assert response['temperature'] == 30.0
    assert response['health_status'] == 1

@patch('your_module.SOMEIPClient', return_value=mock_client)
def test_GetBatteryStatus_high_temperature(mock_someip_client):
    """
    Test the GetBatteryStatus method with high temperature.
    """
    mock_client.methods[1] = Mock(return_value={'soc': 50.0, 'voltage': 420.0, 'current': 10.0, 'temperature': 46.0, 'health_status': 0})
    response = mock_client.methods[1]()
    assert response['soc'] == 50.0
    assert response['voltage'] == 420.0
    assert response['current'] == 10.0
    assert response['temperature'] == 46.0
    assert response['health_status'] == 1

@patch('your_module.SOMEIPClient', return_value=mock_client)
def test_GetBatteryStatus_critical_temperature(mock_someip_client):
    """
    Test the GetBatteryStatus method with critical temperature.
    """
    mock_client.methods[1] = Mock(return_value={'soc': 50.0, 'voltage': 420.0, 'current': 10.0, 'temperature': 61.0, 'health_status': 0})
    response = mock_client.methods[1]()
    assert response['soc'] == 50.0
    assert response['voltage'] == 420.0
    assert response['current'] == 10.0
    assert response['temperature'] == 61.0
    assert response['health_status'] == 2

@patch('your_module.SOMEIPClient', return_value=mock_client)
def test_GetCellVoltages(mock_someip_client):
    """
    Test the GetCellVoltages method with normal values.
    """
    response = mock_client.methods[2]()
    assert len(response['cell_voltages']) == 8
    assert all(voltage == 3.7 for voltage in response['cell_voltages'])

@patch('your_module.SOMEIPClient', return_value=mock_client)
def test_GetEstimatedRange_eco_mode(mock_someip_client):
    """
    Test the GetEstimatedRange method with ECO mode.
    """
    response = mock_client.methods[3](driving_mode=0)
    assert response['range_km'] == 200.0

@patch('your_module.SOMEIPClient', return_value=mock_client)
def test_GetEstimatedRange_normal_mode(mock_someip_client):
    """
    Test the GetEstimatedRange method with NORMAL mode.
    """
    response = mock_client.methods[3](driving_mode=1)
    assert response['range_km'] == 300.0

@patch('your_module.SOMEIPClient', return_value=mock_client)
def test_GetEstimatedRange_sport_mode(mock_someip_client):
    """
    Test the GetEstimatedRange method with SPORT mode.
    """
    response = mock_client.methods[3](driving_mode=2)
    assert response['range_km'] == 400.0