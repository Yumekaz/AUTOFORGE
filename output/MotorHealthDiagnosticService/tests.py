import pytest
from unittest.mock import Mock, patch

# Mock the SOME/IP client to simulate service calls
class MockSOMEIPClient:
    def __init__(self):
        self.events = {}
    
    def subscribe(self, event_id, callback):
        if event_id not in self.events:
            self.events[event_id] = []
        self.events[event_id].append(callback)
    
    def emit_event(self, event_id, data):
        if event_id in self.events:
            for callback in self.events[event_id]:
                callback(data)

# Mock the service implementation
class MotorHealthDiagnosticService:
    def __init__(self, client):
        self.client = client
    
    def GetMotorHealth(self):
        return {
            'motor_temperature': 0.0,
            'motor_torque': 0.0,
            'motor_power': 0.0,
            'health_status': 0
        }
    
    def handle_motor_temperature(self, temperature):
        if temperature > 85:
            self.client.emit_event(33281, {'warning_code': 0x0201, 'warning_message': 'Motor temperature high'})
        elif temperature > 100:
            self.client.emit_event(33281, {'warning_code': 0x0202, 'warning_message': 'Motor critical temperature'})

# Test cases
def test_get_motor_health():
    """Test the GetMotorHealth method"""
    client = MockSOMEIPClient()
    service = MotorHealthDiagnosticService(client)
    
    result = service.GetMotorHealth()
    assert result == {
        'motor_temperature': 0.0,
        'motor_torque': 0.0,
        'motor_power': 0.0,
        'health_status': 0
    }

def test_handle_motor_temperature_high_temp():
    """Test the handle_motor_temperature method with high temperature"""
    client = MockSOMEIPClient()
    service = MotorHealthDiagnosticService(client)
    
    service.handle_motor_temperature(90)
    assert len(client.events[33281]) == 1
    assert client.events[33281][0]['warning_code'] == 0x0201
    assert client.events[33281][0]['warning_message'] == 'Motor temperature high'

def test_handle_motor_temperature_critical_temp():
    """Test the handle_motor_temperature method with critical temperature"""
    client = MockSOMEIPClient()
    service = MotorHealthDiagnosticService(client)
    
    service.handle_motor_temperature(105)
    assert len(client.events[33281]) == 1
    assert client.events[33281][0]['warning_code'] == 0x0202
    assert client.events[33281][0]['warning_message'] == 'Motor critical temperature'

def test_handle_motor_temperature_normal_temp():
    """Test the handle_motor_temperature method with normal temperature"""
    client = MockSOMEIPClient()
    service = MotorHealthDiagnosticService(client)
    
    service.handle_motor_temperature(75)
    assert len(client.events[33281]) == 0