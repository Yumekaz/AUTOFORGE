"""
AUTOFORGE Code Generators
Generates automotive service code for multiple languages.
"""

from typing import Dict, Any, Optional
import yaml

from llm.client import get_client, LLMClient
from llm.prompts import (
    CPP_SOMEIP_TEMPLATE,
    RUST_SOMEIP_TEMPLATE,
    VALIDATION_PROMPT,
)


class BaseCodeGenerator:
    """Base class for all code generators."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_client("gemini")
        self.language = "unknown"
        self.file_extension = ".txt"
        self.min_service_lines = 200

    def generate_service(
        self,
        requirement: Dict[str, Any],
        test_code: str
    ) -> str:
        """Generate service implementation from requirement and tests."""
        raise NotImplementedError

    def validate_code(self, code: str) -> Dict[str, Any]:
        """Validate generated code for syntax and compliance."""
        prompt = VALIDATION_PROMPT.format(code=code, language=self.language)
        response = self.llm.generate(prompt)
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"valid": False, "issues": ["Failed to parse validation response"]}

    def _enforce_min_lines(self, code: str) -> None:
        """Enforce minimum service size for production readiness."""
        line_count = sum(1 for line in code.splitlines() if line.strip())
        if line_count < self.min_service_lines:
            raise ValueError(
                f"{self.language} service too short: {line_count} lines "
                f"(minimum {self.min_service_lines} required)"
            )

    def _service_name(self, requirement: Dict[str, Any]) -> str:
        return (
            requirement.get("service", {}).get("name")
            or requirement.get("service_name")
            or "UnknownService"
        )

    def _service_ids(self, requirement: Dict[str, Any]) -> tuple[str, str]:
        interface = requirement.get("service", {}).get("interface", {})
        service_id = interface.get("service_id", requirement.get("service_id", "0x1234"))
        instance_id = interface.get("instance_id", requirement.get("instance_id", "0x5678"))
        return str(service_id), str(instance_id)

    def _methods(self, requirement: Dict[str, Any]) -> list:
        return (
            requirement.get("service", {}).get("interface", {}).get("methods")
            or requirement.get("methods", [])
        )

    def _events(self, requirement: Dict[str, Any]) -> list:
        return (
            requirement.get("service", {}).get("interface", {}).get("events")
            or requirement.get("events", [])
        )


class CppGenerator(BaseCodeGenerator):
    """C++ SOME/IP code generator."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(llm_client)
        self.language = "C++"
        self.file_extension = ".cpp"

    def generate_service(
        self,
        requirement: Dict[str, Any],
        test_code: str
    ) -> str:
        service_name = self._service_name(requirement)
        service_id, instance_id = self._service_ids(requirement)
        methods_yaml = yaml.dump(self._methods(requirement))
        events_yaml = yaml.dump(self._events(requirement))

        prompt = CPP_SOMEIP_TEMPLATE.format(
            service_name=service_name,
            service_id=service_id,
            instance_id=instance_id,
            methods_yaml=methods_yaml,
            events_yaml=events_yaml,
        )

        full_prompt = f"""
{prompt}

IMPORTANT: The implementation MUST pass these tests:
```cpp
{test_code}
```
"""

        raw_code = self.llm.generate(full_prompt)
        self._enforce_min_lines(raw_code)
        return raw_code


class KotlinGenerator(BaseCodeGenerator):
    """Kotlin code generator for Android Automotive services."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(llm_client)
        self.language = "Kotlin"
        self.file_extension = ".kt"

    def generate_service(
        self,
        requirement: Dict[str, Any],
        test_code: str
    ) -> str:
        service_name = self._service_name(requirement)
        methods_yaml = yaml.dump(self._methods(requirement))

        prompt = f"""
Generate a Kotlin service for Android Automotive:

SERVICE: {service_name}

METHODS:
{methods_yaml}

Requirements:
1. Use Kotlin coroutines for async operations
2. Follow Android Automotive patterns
3. Include proper null safety
4. Use data classes for DTOs
5. Minimum 200 non-empty lines

The implementation MUST pass these tests:
```kotlin
{test_code}
```

Output ONLY Kotlin code.
"""
        raw_code = self.llm.generate(prompt)
        self._enforce_min_lines(raw_code)
        return raw_code


class JavaGenerator(BaseCodeGenerator):
    """Java code generator for Android Automotive services."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(llm_client)
        self.language = "Java"
        self.file_extension = ".java"

    def generate_service(
        self,
        requirement: Dict[str, Any],
        test_code: str
    ) -> str:
        service_name = self._service_name(requirement)
        methods_yaml = yaml.dump(self._methods(requirement))

        prompt = f"""
Generate a Java service for Android Automotive:

SERVICE: {service_name}

METHODS:
{methods_yaml}

Requirements:
1. Use Java 17 compatible code
2. Follow Android Automotive service patterns
3. Include defensive coding and null checks
4. Use POJOs for DTOs
5. Minimum 200 non-empty lines

The implementation MUST pass these tests:
```java
{test_code}
```

Output ONLY Java code.
"""
        raw_code = self.llm.generate(prompt)
        self._enforce_min_lines(raw_code)
        return raw_code


class RustGenerator(BaseCodeGenerator):
    """Rust SOME/IP code generator."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(llm_client)
        self.language = "Rust"
        self.file_extension = ".rs"

    def generate_service(
        self,
        requirement: Dict[str, Any],
        test_code: str
    ) -> str:
        service_name = self._service_name(requirement)
        service_id, instance_id = self._service_ids(requirement)
        methods_yaml = yaml.dump(self._methods(requirement))
        events_yaml = yaml.dump(self._events(requirement))

        prompt = RUST_SOMEIP_TEMPLATE.format(
            service_name=service_name,
            service_id=service_id,
            instance_id=instance_id,
            methods_yaml=methods_yaml,
            events_yaml=events_yaml,
        )

        full_prompt = f"""
{prompt}

IMPORTANT: The implementation MUST pass these tests:
```rust
{test_code}
```
"""

        raw_code = self.llm.generate(full_prompt)
        self._enforce_min_lines(raw_code)
        return raw_code


def get_generator(language: str, llm_client: Optional[LLMClient] = None) -> BaseCodeGenerator:
    """Get a code generator for the specified language."""
    generators = {
        "cpp": CppGenerator,
        "c++": CppGenerator,
        "kotlin": KotlinGenerator,
        "kt": KotlinGenerator,
        "java": JavaGenerator,
        "jav": JavaGenerator,
        "rust": RustGenerator,
        "rs": RustGenerator,
    }

    generator_class = generators.get(language.lower())
    if generator_class is None:
        raise ValueError(f"Unsupported language: {language}")

    return generator_class(llm_client)

