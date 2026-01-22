"""
LLM Client Abstraction for AUTOFORGE
Supports multiple LLM providers with unified interface
"""

import os
from abc import ABC, abstractmethod
from typing import Optional
import yaml


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text from prompt."""
        pass


class GeminiClient(LLMClient):
    """Google Gemini client."""
    
    def __init__(self, model: str = "gemini-1.5-flash", temperature: float = 0.2):
        self.model = model
        self.temperature = temperature
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
            genai.configure(api_key=api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        client = self._get_client()
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
        response = client.generate_content(
            full_prompt,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": 4096,
            }
        )
        return response.text


class OpenAIClient(LLMClient):
    """OpenAI client."""
    
    def __init__(self, model: str = "gpt-4-turbo-preview", temperature: float = 0.2):
        self.model = model
        self.temperature = temperature
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._client = OpenAI(api_key=api_key)
        return self._client
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        client = self._get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=4096,
        )
        return response.choices[0].message.content


class MockClient(LLMClient):
    """Mock client for testing without API calls."""
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # Return mock response based on prompt content
        # Check for test generation prompt specifically
        if "generate comprehensive unit tests" in prompt.lower() or "generate python pytest tests" in prompt.lower():
            return self._mock_test_code()
        elif "generate" in prompt.lower() and "implementation" in prompt.lower():
            # Code generation
            if "cpp" in prompt.lower() or "c++" in prompt.lower():
                return self._mock_cpp_code()
            else:
                return self._mock_python_code()
        elif "cpp" in prompt.lower() or "c++" in prompt.lower():
            return self._mock_cpp_code()
        else:
            return self._mock_python_code()
    
    def _mock_test_code(self) -> str:
        return '''
import pytest

def test_get_battery_status():
    """Test GetBatteryStatus returns valid data."""
    service = BMSDiagnosticService()
    status = service.get_battery_status()
    
    assert 0 <= status.soc <= 100
    assert status.voltage > 0
    assert status.health_status in [0, 1, 2]

def test_low_battery_warning():
    """Test warning emitted when SOC < 20%."""
    service = BMSDiagnosticService()
    service.set_battery_soc(15)
    
    warnings = service.get_warnings()
    assert any(w.code == 0x0001 for w in warnings)
'''
    
    def _mock_cpp_code(self) -> str:
        return '''
#include "bms_diagnostic_service.hpp"
#include <vsomeip/vsomeip.hpp>

class BMSDiagnosticService {
public:
    struct BatteryStatus {
        float soc;
        float voltage;
        float current;
        float temperature;
        uint8_t health_status;
    };
    
    BatteryStatus GetBatteryStatus() {
        BatteryStatus status;
        status.soc = battery_soc_;
        status.voltage = battery_voltage_;
        status.current = battery_current_;
        status.temperature = battery_temperature_;
        status.health_status = CalculateHealthStatus();
        return status;
    }
    
private:
    uint8_t CalculateHealthStatus() {
        if (battery_temperature_ > 60) return 2;  // CRITICAL
        if (battery_temperature_ > 45 || battery_soc_ < 20) return 1;  // WARNING
        return 0;  // OK
    }
    
    float battery_soc_ = 0.0f;
    float battery_voltage_ = 0.0f;
    float battery_current_ = 0.0f;
    float battery_temperature_ = 0.0f;
};
'''
    
    def _mock_python_code(self) -> str:
        return '''
from dataclasses import dataclass
from typing import List
from enum import IntEnum

class HealthStatus(IntEnum):
    OK = 0
    WARNING = 1
    CRITICAL = 2

@dataclass
class BatteryStatus:
    soc: float
    voltage: float
    current: float
    temperature: float
    health_status: HealthStatus

class BMSDiagnosticService:
    def __init__(self):
        self._soc = 0.0
        self._voltage = 0.0
        self._current = 0.0
        self._temperature = 0.0
        
    def get_battery_status(self) -> BatteryStatus:
        return BatteryStatus(
            soc=self._soc,
            voltage=self._voltage,
            current=self._current,
            temperature=self._temperature,
            health_status=self._calculate_health()
        )
    
    def _calculate_health(self) -> HealthStatus:
        if self._temperature > 60:
            return HealthStatus.CRITICAL
        if self._temperature > 45 or self._soc < 20:
            return HealthStatus.WARNING
        return HealthStatus.OK
'''


def get_client(provider: str = "gemini", **kwargs) -> LLMClient:
    """Factory function to get LLM client."""
    clients = {
        "gemini": GeminiClient,
        "openai": OpenAIClient,
        "mock": MockClient,
    }
    
    if provider not in clients:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(clients.keys())}")
    
    return clients[provider](**kwargs)
