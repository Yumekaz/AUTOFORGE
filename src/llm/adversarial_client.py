"""
Adversarial LLM Clients for AUTOFORGE
Implements the core "Adversarial Governance" architecture with separate Auditor and Architect agents.
"""

import os
from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum

from .client import LLMClient, GeminiClient, OpenAIClient, MockClient


class AgentRole(Enum):
    """Adversarial agent roles - the core of AUTOFORGE's innovation."""
    AUDITOR = "auditor"      # Skeptical, strict, generates tests & validates
    ARCHITECT = "architect"  # Creative, implementation-focused, writes code


class AdversarialLLMClient(LLMClient):
    """
    Base class for adversarial LLM clients.
    Adds role-specific system prompts on top of base LLM functionality.
    """
    
    def __init__(self, base_client: LLMClient, role: AgentRole):
        self.base_client = base_client
        self.role = role
        
        # Auditor uses lower temperature (more deterministic/strict)
        # Architect uses higher temperature (more creative)
        if hasattr(self.base_client, 'temperature'):
            self.base_client.temperature = 0.1 if role == AgentRole.AUDITOR else 0.3
    
    def get_role_system_prompt(self) -> str:
        """Get role-specific system prompt that enforces adversarial behavior."""
        if self.role == AgentRole.AUDITOR:
            return """🔴 YOU ARE THE AUDITOR - THE SKEPTICAL SAFETY WATCHDOG

YOUR MISSION:
- Generate COMPREHENSIVE tests that will CATCH bugs and safety violations
- Assume the code generator will try to cut corners or take shortcuts
- Check for MISRA compliance, edge cases, boundary conditions
- Create tests for failure modes (null inputs, overflow, race conditions)
- BE HARSH. Tests should be UNFORGIVING and EXHAUSTIVE.

MINDSET:
You are NOT here to help the architect succeed. You are here to EXPOSE flaws.
Every line of generated code is GUILTY until proven innocent by passing ALL your tests.

TEST COVERAGE REQUIREMENTS:
- 100% branch coverage minimum
- All edge cases (min/max values, nulls, empty arrays)
- All business rules from requirements
- All safety-critical scenarios (temperature limits, battery critical states)
- Error handling and exception paths

OUTPUT FORMAT:
Generate ONLY the test code. No explanations. Pure executable tests."""
        
        else:  # ARCHITECT
            return """🟢 YOU ARE THE ARCHITECT - THE CODE IMPLEMENTATION EXPERT

YOUR MISSION:
- Write clean, safe, production-quality code that PASSES EVERY TEST
- You MUST satisfy ALL tests from the Auditor - there is NO ROOM FOR FAILURE
- Your code will be AUTOMATICALLY REJECTED if it fails any test
- Follow MISRA guidelines, automotive safety standards
- Handle all edge cases identified in the tests

CONSTRAINTS:
- Code must compile/run without errors
- Must pass 100% of unit tests
- Must pass static analysis (MISRA for C++, pylint for Python)
- No shortcuts, no hardcoded values that "trick" the tests
- Proper error handling for all failure modes

MINDSET:
The Auditor has already written strict tests. Your job is to write code SO GOOD
that it passes every single one. This is production automotive code - lives depend on it.

OUTPUT FORMAT:
Generate ONLY the implementation code. No explanations. Pure executable code."""
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text with role-specific system prompt prepended.
        """
        role_prompt = self.get_role_system_prompt()
        
        # Combine role prompt with optional custom system prompt
        if system_prompt:
            full_system = f"{role_prompt}\n\n{system_prompt}"
        else:
            full_system = role_prompt
        
        return self.base_client.generate(prompt, system_prompt=full_system)


# ============================================================================
# Factory Functions - Primary API for Pipeline
# ============================================================================

def get_auditor(provider: str = "gemini", **kwargs) -> AdversarialLLMClient:
    """
    Factory function to create AUDITOR agent (strict, skeptical, test generator).
    
    The Auditor's job:
    - Generate comprehensive tests BEFORE any code is written
    - Check for edge cases, safety violations, MISRA compliance
    - Validate final code and REJECT if tests fail
    
    Args:
        provider: "gemini", "openai", or "mock"
        **kwargs: Additional arguments for base client
    
    Returns:
        AdversarialLLMClient configured as AUDITOR
    """
    if provider == "gemini":
        base = GeminiClient(temperature=0.1, **kwargs)
    elif provider == "openai":
        base = OpenAIClient(temperature=0.1, **kwargs)
    elif provider == "mock":
        base = MockClient(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    return AdversarialLLMClient(base, AgentRole.AUDITOR)


def get_architect(provider: str = "gemini", **kwargs) -> AdversarialLLMClient:
    """
    Factory function to create ARCHITECT agent (creative, implementation-focused).
    
    The Architect's job:
    - Write implementation code that PASSES all tests from Auditor
    - Follow automotive safety standards (MISRA, ASPICE)
    - Handle all edge cases identified by Auditor
    - Code must be production-ready
    
    Args:
        provider: "gemini", "openai", or "mock"
        **kwargs: Additional arguments for base client
    
    Returns:
        AdversarialLLMClient configured as ARCHITECT
    """
    if provider == "gemini":
        base = GeminiClient(temperature=0.3, **kwargs)
    elif provider == "openai":
        base = OpenAIClient(temperature=0.3, **kwargs)
    elif provider == "mock":
        base = MockClient(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    return AdversarialLLMClient(base, AgentRole.ARCHITECT)


# ============================================================================
# Example Usage
# ============================================================================
if __name__ == "__main__":
    # This demonstrates the adversarial approach
    
    auditor = get_auditor("mock")
    architect = get_architect("mock")
    
    print("=" * 60)
    print("PHASE 1: AUDITOR GENERATES TESTS")
    print("=" * 60)
    
    tests = auditor.generate("""
    Generate pytest tests for a Battery Management System service with:
    - GetBatteryStatus() method
    - Low battery warning at SOC < 20%
    - Critical temperature alert at temp > 60°C
    """)
    
    print(tests)
    
    print("\n" + "=" * 60)
    print("PHASE 2: ARCHITECT IMPLEMENTS CODE TO PASS TESTS")
    print("=" * 60)
    
    code = architect.generate(f"""
    Generate implementation for the Battery Management System.
    
    TESTS TO PASS:
    {tests}
    
    Your code MUST pass ALL these tests.
    """)
    
    print(code)
    
    print("\n" + "=" * 60)
    print("PHASE 3: AUDITOR VALIDATES (Would run actual tests here)")
    print("=" * 60)
