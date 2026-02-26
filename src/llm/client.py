"""
LLM Client Abstraction for AUTOFORGE
Supports multiple LLM providers with unified interface
"""

import os
import json
import warnings
from abc import ABC, abstractmethod
from typing import Optional
import yaml
import urllib.request
import urllib.error

# Suppress noisy upstream deprecation warning from google-generativeai package.
warnings.filterwarnings(
    "ignore",
    message=r".*google\.generativeai.*",
    category=FutureWarning,
)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text from prompt."""
        pass


class GeminiClient(LLMClient):
    """Google Gemini client."""
    
    def __init__(self, model: str = "gemini-2.5-flash", temperature: float = 0.2):
        self.model = model
        self.temperature = temperature
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            # Suppress upstream deprecation warning noise in CLI output.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", FutureWarning)
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


class OllamaClient(LLMClient):
    """Ollama client for local Llama models."""
    
    def __init__(
        self,
        model: str = "qwen2.5-coder:7b",
        host: str = "http://localhost:11434",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout_seconds: int = 420,
    ):
        self.model = model
        self.host = host.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        # Allow runtime override for slower local inference machines.
        env_timeout = os.getenv("OLLAMA_TIMEOUT_SECONDS")
        if env_timeout:
            try:
                timeout_seconds = int(env_timeout)
            except ValueError:
                pass
        self.timeout_seconds = timeout_seconds
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        
        url = f"{self.host}/api/generate"
        response = _post_json(url, payload, timeout_seconds=self.timeout_seconds)
        return response.get("response", "")


class GroqClient(LLMClient):
    """Groq client for Llama models via Groq API."""
    
    def __init__(
        self,
        model: str = "llama-3.1-8b-instant",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        base_url: str = "https://api.groq.com/openai/v1/chat/completions",
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = _post_json(self.base_url, payload, headers=headers)
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")


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
        "ollama": OllamaClient,
        "groq": GroqClient,
        "mock": MockClient,
    }
    
    if provider not in clients:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(clients.keys())}")
    
    return clients[provider](**kwargs)


def _post_json(
    url: str,
    payload: dict,
    headers: Optional[dict] = None,
    timeout_seconds: int = 60,
) -> dict:
    """Post JSON and return parsed JSON response."""
    data = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    request = urllib.request.Request(url, data=data, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"HTTPError {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"URLError: {e}") from e
