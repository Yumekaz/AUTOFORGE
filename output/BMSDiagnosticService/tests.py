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
            "soc": 50.0,
            "voltage": 420.0,
            "current": 10.0,
            "temperature": 30.0,
            "health_status": 0
        }
    
    def GetCellVoltages(self, *args, **kwargs):
        return {
            "cell_voltages": [3.7, 3.8, 3.9]
        }
    
    def GetEstimatedRange(self, driving_mode=1, *args, **kwargs):
        if driving_mode == 0:
            return {"range_km": 200.0}
        elif driving_mode == 1:
            return {"range_km": 300.0}
        elif driving_mode == 2:
            return {"range_km": 400.0}

# Mock the BatteryWarning event
class MockBatteryWarningEvent:
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

# Test class for BMSDiagnosticService
class TestBMSDiagnosticService:
    @pytest.fixture
    def client(self):
        return MockSOMEIPClient()
    
    @pytest.fixture
    def event_emitter(self):
        return MockBatteryWarningEvent
    
    @patch('someip_client.SomeIPClient', new_callable=MockSOMEIPClient)
    def test_GetBatteryStatus(self, mock_client):
        """Test the GetBatteryStatus method"""
        result = mock_client.methods[1]()
        assert result["soc"] == 50.0
        assert result["voltage"] == 420.0
        assert result["current"] == 10.0
        assert result["temperature"] == 30.0
        assert result["health_status"] == 0
    
    @patch('someip_client.SomeIPClient', new_callable=MockSOMEIPClient)
    def test_GetCellVoltages(self, mock_client):
        """Test the GetCellVoltages method"""
        result = mock_client.methods[2]()
        assert result["cell_voltages"] == [3.7, 3.8, 3.9]
    
    @patch('someip_client.SomeIPClient', new_callable=MockSOMEIPClient)
    def test_GetEstimatedRange_ECO(self, mock_client):
        """Test the GetEstimatedRange method with ECO mode"""
        result = mock_client.methods[3](driving_mode=0)
        assert result["range_km"] == 200.0
    
    @patch('someip_client.SomeIPClient', new_callable=MockSOMEIPClient)
    def test_GetEstimatedRange_NORMAL(self, mock_client):
        """Test the GetEstimatedRange method with NORMAL mode"""
        result = mock_client.methods[3](driving_mode=1)
        assert result["range_km"] == 300.0
    
    @patch('someip_client.SomeIPClient', new_callable=MockSOMEIPClient)
    def test_GetEstimatedRange_SPORT(self, mock_client):
        """Test the GetEstimatedRange method with SPORT mode"""
        result = mock_client.methods[3](driving_mode=2)
        assert result["range_km"] == 400.0
    
    @patch('someip_client.SomeIPClient', new_callable=MockSOMEIPClient)
    def test_low_battery_warning(self, mock_client):
        """Test the low battery warning condition"""
        mock_client.methods[1] = Mock(return_value={"soc": 15.0})
        with pytest.raises(MockBatteryWarningEvent) as e:
            mock_client.methods[1]()
        assert e.value.code == 0x0001
        assert e.value.msg == 'Low battery'
    
    @patch('someip_client.SomeIPClient', new_callable=MockSOMEIPClient)
    def test_high_temp_warning(self, mock_client):
        """Test the high temperature warning condition"""
        mock_client.methods[1] = Mock(return_value={"temperature": 50.0})
        with pytest.raises(MockBatteryWarningEvent) as e:
            mock_client.methods[1]()
        assert e.value.code == 0x0002
        assert e.value.msg == 'High temperature'
    
    @patch('someip_client.SomeIPClient', new_callable=MockSOMEIPClient)
    def test_critical_temp_shutdown(self, mock_client):
        """Test the critical temperature shutdown condition"""
        mock_client.methods[1] = Mock(return_value={"temperature": 65.0})
        with pytest.raises(MockBatteryWarningEvent) as e:
            mock_client.methods[1]()
        assert e.value.code == 0x0003
        assert e.value.msg == 'Critical temperature - shutdown required'