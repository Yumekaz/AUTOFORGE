"""
AUTOFORGE - C++ Code Generator
Generates SOME/IP services with MISRA compliance
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml

from llm.client import get_client, LLMClient
from llm.prompts import (
    CPP_SOMEIP_TEMPLATE,
    RUST_SOMEIP_TEMPLATE,
    CODE_GENERATION_PROMPT,
    VALIDATION_PROMPT
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
        prompt = VALIDATION_PROMPT.format(
            code=code,
            language=self.language
        )
        response = self.llm.generate(prompt)
        # Parse JSON response
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


class CppGenerator(BaseCodeGenerator):
    """
    C++ Code Generator for SOME/IP Services
    
    Features:
    - vsomeip library integration
    - MISRA C++ compliance
    - Header/Implementation separation
    - Proper memory management
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(llm_client)
        self.language = "C++"
        self.file_extension = ".cpp"
        self.header_extension = ".hpp"
        
        # vsomeip standard headers
        self.vsomeip_headers = [
            "#include <vsomeip/vsomeip.hpp>",
            "#include <vsomeip/primitive_types.hpp>",
            "#include <vsomeip/enumeration_types.hpp>",
        ]
        
        # MISRA compliance headers
        self.misra_headers = [
            "#include <cstdint>      // MISRA: Use fixed-width integers",
            "#include <memory>       // MISRA: Smart pointers for memory safety",
            "#include <string>       // MISRA: std::string over char*",
            "#include <vector>       // MISRA: std::vector over raw arrays",
            "#include <functional>   // MISRA: std::function for callbacks",
        ]
    
    def generate_service(
        self,
        requirement: Dict[str, Any],
        test_code: str
    ) -> str:
        """
        Generate a C++ SOME/IP service implementation.
        
        Args:
            requirement: Parsed YAML requirement specification
            test_code: Generated test code that implementation must pass
            
        Returns:
            Generated C++ source code
        """
        service_name = requirement.get("service_name", "UnknownService")
        service_id = requirement.get("service_id", "0x1234")
        instance_id = requirement.get("instance_id", "0x5678")
        
        # Format methods and events for template
        methods_yaml = yaml.dump(requirement.get("methods", []))
        events_yaml = yaml.dump(requirement.get("events", []))
        
        # Generate using SOME/IP template
        prompt = CPP_SOMEIP_TEMPLATE.format(
            service_name=service_name,
            service_id=service_id,
            instance_id=instance_id,
            methods_yaml=methods_yaml,
            events_yaml=events_yaml
        )
        
        # Add test context for adversarial generation
        full_prompt = f"""
{prompt}

IMPORTANT: The implementation MUST pass these tests:
```cpp
{test_code}
```

Ensure all test assertions will pass with proper threshold handling.
"""
        
        # Generate code
        raw_code = self.llm.generate(full_prompt)
        
        # Post-process: ensure vsomeip headers are present
        code = self._ensure_headers(raw_code)

        # Enforce production-quality size
        self._enforce_min_lines(code)
        
        return code
    
    def _ensure_headers(self, code: str) -> str:
        """Ensure all required headers are present."""
        lines = code.split('\n')
        
        # Check for vsomeip include
        has_vsomeip = any('vsomeip' in line for line in lines)
        
        if not has_vsomeip:
            # Find the first #include or add at top
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('#include'):
                    insert_idx = i
                    break
            
            # Insert vsomeip headers
            for header in reversed(self.vsomeip_headers):
                lines.insert(insert_idx, header)
        
        return '\n'.join(lines)
    
    def generate_header(
        self,
        requirement: Dict[str, Any]
    ) -> str:
        """Generate the .hpp header file."""
        service_name = requirement.get("service_name", "UnknownService")
        guard_name = f"{service_name.upper()}_HPP"
        
        header = f"""
#ifndef {guard_name}
#define {guard_name}

{chr(10).join(self.misra_headers)}

{chr(10).join(self.vsomeip_headers)}

namespace autoforge {{
namespace {service_name.lower()} {{

/**
 * @brief {service_name} - SOME/IP Service Interface
 * 
 * Auto-generated by AUTOFORGE
 * MISRA C++ Compliant
 */
class {service_name} {{
public:
    {service_name}();
    ~{service_name}();
    
    // Disable copy (MISRA Rule 12-8-1)
    {service_name}(const {service_name}&) = delete;
    {service_name}& operator=(const {service_name}&) = delete;
    
    // Service lifecycle
    bool Initialize();
    void Shutdown();
    
    // Generated methods will be added here
    
private:
    std::shared_ptr<vsomeip::application> app_;
    bool is_initialized_{{false}};
}};

}}  // namespace {service_name.lower()}
}}  // namespace autoforge

#endif  // {guard_name}
"""
        return header


class KotlinGenerator(BaseCodeGenerator):
    """
    Kotlin Code Generator for Android Automotive Services
    
    Features:
    - Coroutines for async operations
    - Flow/LiveData for reactive data
    - Android Automotive patterns
    - Null safety
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(llm_client)
        self.language = "Kotlin"
        self.file_extension = ".kt"
        
        # Standard Android Automotive imports
        self.standard_imports = [
            "import kotlinx.coroutines.*",
            "import kotlinx.coroutines.flow.*",
            "import androidx.lifecycle.ViewModel",
            "import androidx.lifecycle.viewModelScope",
            "import androidx.car.app.CarContext",
        ]
    
    def generate_service(
        self,
        requirement: Dict[str, Any],
        test_code: str
    ) -> str:
        """
        Generate a Kotlin service for Android Automotive.
        
        Args:
            requirement: Parsed YAML requirement specification
            test_code: Generated test code that implementation must pass
            
        Returns:
            Generated Kotlin source code
        """
        service_name = requirement.get("service_name", "UnknownService")
        methods_yaml = yaml.dump(requirement.get("methods", []))
        
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
5. Implement StateFlow for reactive updates

The implementation MUST pass these tests:
```kotlin
{test_code}
```

Output ONLY the Kotlin code with proper package declaration.
"""
        
        raw_code = self.llm.generate(prompt)
        code = self._ensure_imports(raw_code)

        # Enforce production-quality size
        self._enforce_min_lines(code)
        
        return code


class RustGenerator(BaseCodeGenerator):
    """
    Rust Code Generator for SOME/IP Services

    Features:
    - serde serialization
    - Result/Option patterns
    - Error handling
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(llm_client)
        self.language = "Rust"
        self.file_extension = ".rs"

    def generate_service(
        self,
        requirement: Dict[str, Any],
        test_code: str
    ) -> str:
        service_name = requirement.get("service_name", "UnknownService")
        service_id = requirement.get("service_id", "0x1234")
        instance_id = requirement.get("instance_id", "0x5678")

        methods_yaml = yaml.dump(requirement.get("methods", []))
        events_yaml = yaml.dump(requirement.get("events", []))

        prompt = RUST_SOMEIP_TEMPLATE.format(
            service_name=service_name,
            service_id=service_id,
            instance_id=instance_id,
            methods_yaml=methods_yaml,
            events_yaml=events_yaml
        )

        full_prompt = f"""
{prompt}

IMPORTANT: The implementation MUST pass these tests:
```rust
{test_code}
```

Ensure all test assertions will pass with proper threshold handling.
"""

        raw_code = self.llm.generate(full_prompt)
        self._enforce_min_lines(raw_code)
        return raw_code
    
    def _ensure_imports(self, code: str) -> str:
        """Ensure all required imports are present."""
        lines = code.split('\n')
        
        # Check for coroutines import
        has_coroutines = any('kotlinx.coroutines' in line for line in lines)
        
        if not has_coroutines:
            # Find package declaration and add imports after
            package_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('package'):
                    package_idx = i + 1
                    break
            
            # Insert blank line and imports
            lines.insert(package_idx, "")
            for j, imp in enumerate(self.standard_imports):
                lines.insert(package_idx + 1 + j, imp)
        
        return '\n'.join(lines)


# Factory function
def get_generator(language: str, llm_client: Optional[LLMClient] = None) -> BaseCodeGenerator:
    """Get a code generator for the specified language."""
    generators = {
        "cpp": CppGenerator,
        "c++": CppGenerator,
        "kotlin": KotlinGenerator,
        "kt": KotlinGenerator,
        "rust": RustGenerator,
        "rs": RustGenerator,
    }
    
    generator_class = generators.get(language.lower())
    if generator_class is None:
        raise ValueError(f"Unsupported language: {language}")
    
    return generator_class(llm_client)
