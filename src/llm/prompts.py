"""
Prompt Templates for AUTOFORGE
Test-First approach: Generate tests before implementation
"""

SYSTEM_PROMPT = """You are an expert automotive software engineer specializing in:
- Service-Oriented Architecture (SoA) for vehicles
- SOME/IP protocol implementation
- MISRA C++ compliance
- ASPICE development processes

You write clean, well-documented, production-quality code.
You always follow the test-first approach: tests define the expected behavior.
"""

TEST_GENERATION_PROMPT = """
Based on the following service requirement, generate comprehensive unit tests.

SERVICE REQUIREMENT:
{requirement_yaml}

Generate Python pytest tests that:
1. Test all methods defined in the interface
2. Test edge cases (boundary values, error conditions)
3. Test the business rules defined
4. Include docstrings explaining what each test verifies

IMPORTANT:
- Tests should be runnable without the actual implementation
- Use mocking where appropriate
- Follow AAA pattern (Arrange, Act, Assert)
- Include at least one test per method and one per business rule

Output ONLY the Python test code, no explanations.
"""

CODE_GENERATION_PROMPT = """
Based on the following service requirement and tests, generate the implementation.

SERVICE REQUIREMENT:
{requirement_yaml}

TESTS TO PASS:
{test_code}

Generate {language} code that:
1. Implements all methods defined in the interface
2. Passes ALL the provided tests
3. Follows {language} best practices
4. Includes proper error handling
5. Is MISRA compliant (for C++)

TARGET PROTOCOL: {protocol}

Output ONLY the {language} code, no explanations.
"""

CPP_SOMEIP_TEMPLATE = """
Generate a C++ SOME/IP service skeleton for:

SERVICE: {service_name}
SERVICE_ID: {service_id}
INSTANCE_ID: {instance_id}

METHODS:
{methods_yaml}

EVENTS:
{events_yaml}

Requirements:
1. Use vsomeip library patterns
2. Include proper SOME/IP serialization
3. Follow MISRA C++ guidelines
4. Include header guards and includes
5. Separate .hpp and .cpp files

Output format:
```hpp
// Header file content
```

```cpp
// Implementation file content
```
"""

RUST_SOMEIP_TEMPLATE = """
Generate a Rust SOME/IP service for:

SERVICE: {service_name}
SERVICE_ID: {service_id}
INSTANCE_ID: {instance_id}

METHODS:
{methods_yaml}

Requirements:
1. Use appropriate Rust patterns (Result, Option)
2. Include proper error handling
3. Use serde for serialization
4. Follow Rust naming conventions

Output ONLY the Rust code.
"""

KOTLIN_SERVICE_TEMPLATE = """
Generate a Kotlin service for Android Automotive:

SERVICE: {service_name}

METHODS:
{methods_yaml}

Requirements:
1. Use Kotlin coroutines for async operations
2. Follow Android Automotive patterns
3. Include proper null safety
4. Use data classes for DTOs

Output ONLY the Kotlin code.
"""

HMI_DASHBOARD_TEMPLATE = """
Generate a React dashboard component for vehicle health monitoring.

SIGNALS TO DISPLAY:
{signals}

REQUIREMENTS:
1. Modern React with hooks
2. Tailwind CSS for styling
3. Real-time data display
4. Color-coded status indicators (green/yellow/red)
5. Responsive design

Output a single React component file.
"""

ANDROID_HMI_TEMPLATE = """
Generate an Android Jetpack Compose UI for vehicle health monitoring.

SIGNALS TO DISPLAY:
{signals}

REQUIREMENTS:
1. Use Kotlin and Jetpack Compose
2. Follow Android Automotive OS Design Guidelines
3. Real-time data observation (LiveData/Flow)
4. Dark theme (automotive standard)
5. Large touch targets for driver safety

Output a single Kotlin file with the Composable function.
"""

ML_WRAPPER_TEMPLATE = """
Generate a C++ ONNX Runtime inference wrapper for:

MODEL: {model_name}
MODEL_PATH: {model_path}

INPUT SIGNALS:
{inputs}

OUTPUT STRUCTURE:
{outputs}

REQUIREMENTS:
1. Use Microsoft ONNX Runtime C++ API (Ort::Session, Ort::Value)
2. Map vehicle signal floats to input Ort::Value tensors
3. Return inference results as a typed struct
4. Include proper error handling for model loading
5. Use RAII for resource management
6. Thread-safe for real-time vehicle systems

Output ONLY the C++ header file (.hpp) with the wrapper class.
"""

VALIDATION_PROMPT = """
Review the following generated code for issues:

CODE:
{code}

LANGUAGE: {language}

Check for:
1. Syntax errors
2. Missing imports/includes
3. MISRA violations (for C++)
4. Logic errors based on the requirements
5. Missing error handling

Output a JSON object:
{{
    "valid": true/false,
    "issues": ["issue1", "issue2", ...],
    "suggestions": ["suggestion1", ...]
}}
"""
