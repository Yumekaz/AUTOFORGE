<p align="center">
  <img src="https://img.shields.io/badge/TELIPORT-Season%203-blue?style=for-the-badge" alt="TELIPORT Season 3"/>
  <img src="https://img.shields.io/badge/Case%20Study-2-green?style=for-the-badge" alt="Case Study 2"/>
  <img src="https://img.shields.io/badge/Status-Competition%20Ready-success?style=for-the-badge" alt="Status"/>
</p>

<h1 align="center">🚗 AUTOFORGE</h1>
<h3 align="center">Adversarial GenAI Pipeline for Automotive SDV Code Generation</h3>

<p align="center">
  <strong>Test-First • Self-Healing • ASIL-D Evidence • ASPICE/MISRA Aligned</strong>
</p>

---

## 🎯 What is AUTOFORGE?

**AUTOFORGE** is a **first-of-its-kind adversarial GenAI pipeline** that generates production-ready automotive software using **two competing AI agents**:

| Agent | Role | Behavior |
|-------|------|----------|
| 🔍 **The Auditor** | Skeptical & Strict | Generates strict tests FIRST |
| 🏗️ **The Architect** | Creative & Focused | Writes code to pass ALL tests |
| 🚦 **Validation Gate** | Automated Guardian | Runs static analysis, auto-rejects failures |

### Core Insight: Adversarial Governance

> **GenAI cannot check its own work.**
> 
> We use **SEPARATE agents** with **OPPOSING roles**:
> - The Auditor tries to **BREAK** the code with strict tests
> - The Architect must **SATISFY** every test
> - The Gate **REJECTS** code that fails validation
>
> This adversarial approach eliminates hallucinations and ensures production-quality code.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    INPUT: Requirements (YAML)                     │
│              (Service definitions, SOME/IP interfaces)            │
└────────────────────────────┬─────────────────────────────────────┘
                             ↓
              ┌──────────────────────────────┐
              │    PHASE 1: AUDITOR AGENT    │  🔍 Skeptical
              │    Generates Tests FIRST     │
              │    (100% Requirement Cover)  │
              └──────────────┬───────────────┘
                             ↓
                  [Test Suite Generated]
                             ↓
              ┌──────────────────────────────┐
              │   PHASE 2: ARCHITECT AGENT   │  🏗️ Creative
              │   Generates Implementation   │
              │   (Must Pass ALL Tests)      │
              └──────────────┬───────────────┘
                             ↓
                [Implementation Code]
                             ↓
              ┌──────────────────────────────┐
              │   PHASE 3: VALIDATION GATE   │  🚦 Automated
              │   • pytest (unit tests)      │
              │   • clang-tidy (MISRA C++)   │
              │   • pylint (static analysis) │
              │   • ASPICE traceability      │
              └──────────────┬───────────────┘
                             │
                   ┌─────────┴─────────┐
                   ↓                   ↓
              ❌ FAIL              ✅ PASS
          (Auto-Retry ×3)     (Output + Trace)
                   │                   │
                   ↓                   ↓
         [Error Context to LLM]   [Production Ready]
```

---

## ✨ Key Features

### 🔄 Self-Healing Loop
- **Automatic retry** on validation failure (up to 3 attempts)
- **Error context injection** - failed tests/lint errors fed back to LLM
- **Audit trail** - complete trace of all attempts in `audit_report.json`

### 🛡️ Automotive Compliance
- **MISRA C++** static analysis via clang-tidy (MISRA-aligned checks)
- **ASIL-D** automated validation (heuristics + clang static analyzer)
- **ASPICE traceability** - requirements → design → tests → code (SWE.3 matrix)
- **Deterministic validation** - no hallucinated "pass" results

### 🚀 Multi-Target Code Generation
| Output Type | Technologies |
|-------------|--------------|
| **Services** | C++ (SOME/IP), Rust, Kotlin |
| **HMI** | Android Jetpack Compose, React |
| **ML Integration** | ONNX Runtime C++ wrappers |
| **Deployment** | Docker, OTA manifests |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Gemini API key (or use `--mock` mode)
- Docker (optional, recommended)
- (Optional) clang, clang-tidy, cppcheck for validation
- (Optional) rustc for Rust validation

### Installation

```bash
# Clone the repository
git clone https://github.com/Yumekaz/AUTOFORGE.git
cd autoforge

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Install C++ validation tools
# Ubuntu/Debian:
sudo apt-get install clang-tidy cppcheck
# Windows: Install LLVM from https://llvm.org/

# Set your API key
export GOOGLE_API_KEY="your-gemini-api-key"
```

### Run Your First Pipeline

```bash
# Run with demo (BMS Diagnostic Service)
python main.py --demo bms

# Or run without API key (mock mode)
python main.py --demo bms --mock

# Run with custom requirement
python main.py --requirement input/requirements/bms_diagnostic.yaml
```

### Benchmark LLMs (Round 2 Evidence)
```bash
# Dry run (no API calls) - generates table + JSON
python scripts/benchmark.py --dry-run

# Real run (requires API keys + Ollama/Groq)
python scripts/benchmark.py --runs 20 --providers gemini,ollama,groq
```

### CARLA Integration (Round 2 Evidence)
```bash
# Start REST stub for CARLA demo (CPU-only)
python integrations/service_stub/rest_bms_service.py

# Run CARLA bridge (writes output/carla_validation.json)
python integrations/carla_bridge/carla_integration.py --log-path output/carla_validation.json
```

### Docker (Recommended)

```bash
# Build the container
docker build -t autoforge:v1.0 .

# Run with API key
docker run --rm -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  -v $(pwd)/output:/autoforge/output \
  autoforge:v1.0 --demo bms

# Run without API key (mock mode)
docker run --rm \
  -v $(pwd)/output:/autoforge/output \
  autoforge:v1.0 --demo bms --mock
```

---

## 📁 Project Structure

```
autoforge/
├── main.py                          # 🚀 Entry point
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Container build
├── docker-compose.yml               # Multi-service orchestration
│
├── config/
│   ├── llm_config.yaml              # LLM settings (model, temperature)
│   └── vehicle_signals.yaml         # 25+ vehicle signal definitions
│
├── input/
│   └── requirements/
│       └── bms_diagnostic.yaml      # Example: BMS service requirement
│
├── src/
│   ├── pipeline/
│   │   ├── orchestrator.py          # Main pipeline execution
│   │   └── validation_gate.py       # Test/lint/MISRA validation
│   ├── codegen/
│   │   ├── generators.py            # Multi-language code generators
│   │   └── ota/                      # OTA manifest generation
│   └── llm/
│       ├── client.py                # LLM API abstraction
│       ├── adversarial_client.py    # Auditor/Architect agent logic
│       └── prompts.py               # Specialized prompts per role
│
├── integrations/
│   └── carla_bridge/
│       └── carla_integration.py     # CARLA simulator bridge
├── integrations/
│   └── service_stub/
│       └── rest_bms_service.py      # REST stub for CARLA demo
│
├── output/                          # Generated code output
│   ├── BMSDiagnosticService/        # C++ SOME/IP service
│   │   ├── services/                # Implementation
│   │   ├── tests/                   # Generated tests
│   │   ├── trace.yaml               # ASPICE traceability
│   │   └── audit_report.json        # Pipeline audit log
│   ├── hmi/
│   │   └── BmsGauge.kt              # Android Jetpack Compose UI
│   └── ml/
│       └── tire_failure_inference.hpp  # ONNX C++ wrapper
├── slide_assets/
│   ├── README.md                    # Slide evidence pointers
│   └── slide_snippets.md            # Copy/paste slide text
│
└── tests/                           # Pipeline unit tests
```

---

## 📋 Requirement YAML Format

AUTOFORGE accepts requirement files in YAML format:

```yaml
service:
  name: BMSDiagnosticService
  description: Battery Management System diagnostic service
  version: "1.0.0"
  language: cpp           # cpp, rust, kotlin, python
  protocol: someip        # someip, dds, rest

  interface:
    service_id: 0x1001
    instance_id: 0x0001
    
    methods:
      - name: GetBatteryStatus
        id: 0x0001
        output:
          - name: soc
            type: float
          - name: health_status
            type: uint8

    events:
      - name: BatteryWarning
        id: 0x8001
        fields:
          - name: warning_code
            type: uint16

  input_signals:
    - battery_soc
    - battery_voltage
    - battery_temperature

  rules:
    - name: low_battery_warning
      condition: "battery_soc < 20"
      action: "emit BatteryWarning(code=0x0001)"

traceability:
  requirement_id: REQ-BMS-001
  aspice_reference: SWE.3
  misra_compliance: required
```

---

## 🎨 Generated Code Examples

### C++ SOME/IP Service
```cpp
class BMSDiagnosticService : public BMSDiagnosticServiceSkeleton {
public:
    ara::core::Future<BatteryStatus> GetBatteryStatus() override {
        BatteryStatus status;
        status.soc = battery_soc_;
        status.voltage = battery_voltage_;
        status.health_status = EvaluateBatteryHealth();
        return ara::core::MakeReadyFuture(status);
    }
};
```

### Android Jetpack Compose HMI
```kotlin
@Composable
fun BmsGauge(stateOfCharge: Float, alertLevel: AlertLevel) {
    val animatedSoC by animateFloatAsState(targetValue = stateOfCharge)
    
    Canvas(modifier = Modifier.fillMaxSize()) {
        drawArc(color = gaugeColor, sweepAngle = (animatedSoC / 100f) * 270f)
    }
}
```

### ML ONNX Integration (C++)
```cpp
class TireFailureInference {
public:
    TireFailurePrediction predict(const TirePressureInput& input) {
        std::array<float, 6> input_data = {
            input.tire_pressure_fl, input.tire_pressure_fr,
            input.tire_pressure_rl, input.tire_pressure_rr
        };
        auto output = session_->Run(/*...*/);
        return prediction;
    }
};
```

---

## 🧪 Validation & Compliance

### Automated Validation Gate

| Check | Tool | Standard |
|-------|------|----------|
| Unit Tests | pytest | 100% requirement coverage |
| Static Analysis | pylint | PEP8/Clean Code |
| MISRA C++ | clang-tidy | MISRA-aligned checks |
| ASIL-D | clang analyzer + heuristics | ISO 26262 evidence |
| Syntax Check | g++/clang | C++17 |
| Traceability | Custom | ASPICE SWE.3 (matrix) |

### Audit Report Example

```json
{
  "trace_id": "TRACE-20231027-BMS-001",
  "final_status": "ACCEPTED",
  "total_attempts": 2,
  "phases": [
    {"phase_id": 3, "status": "FAILED", "misra_compliance": "FAIL"},
    {"phase_id": 4, "status": "SUCCESS", "misra_compliance": "PASS"}
  ],
  "compliance_summary": {
    "misra_rules_checked": 143,
    "misra_violations": 0,
    "requirement_coverage": "100%"
  }
}
```

---

## 🔧 Configuration

### LLM Configuration (`config/llm_config.yaml`)

```yaml
provider: gemini              # gemini, openai, mock
model: gemini-1.5-pro
temperature: 0.2              # Low for deterministic code
max_tokens: 8192
retry_count: 3
```

### Supported Vehicle Signals (`config/vehicle_signals.yaml`)

| Category | Signals |
|----------|---------|
| **Powertrain** | vehicle_speed, engine_rpm, throttle_position, brake_pressure |
| **Battery/EV** | battery_soc, battery_voltage, battery_current, battery_temperature |
| **Tire** | tire_pressure_fl/fr/rl/rr, tire_temperature |
| **Motor** | motor_temperature, motor_torque, motor_power |
| **Environment** | ambient_temperature, odometer |

---

## 🔌 CARLA Integration

AUTOFORGE includes a CARLA simulator bridge for real-time testing:

```bash
# Start CARLA bridge
python integrations/carla_bridge/carla_integration.py --host localhost --port 2000

# Streams vehicle signals to generated services
# Validates BMS predictions against simulated data
```

Evidence output:
- `output/carla_validation.json` (latency + response log)

---

## 📊 Case Study 2 Coverage

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| SoA Services | SOME/IP C++ skeleton generation | ✅ |
| Multi-Protocol | SOME/IP, DDS, REST adapters | ✅ |
| Multi-Language | C++, Rust, Kotlin, Python | ✅ |
| HMI Visualization | Android Jetpack Compose gauges | ✅ |
| Predictive Analytics | ONNX ML integration | ✅ |
| MISRA Compliance | clang-tidy validation gate | ✅ |
| ASIL-D Validation | heuristics + clang analyzer | ✅ |
| ASPICE Traceability | traceability_matrix.csv/yaml | ✅ |
| OTA Updates | Manifest + subscription tiers | ✅ |
| Vehicle Variants | Signal schema abstraction | ✅ |
| CARLA Integration | Real-time simulation bridge | ✅ |
| Benchmarking | benchmark_results.json | ✅ |

---

## 🏆 TATA ELXSI TELIPORT Season 3

This project is our submission for **TELIPORT Season 3 - Case Study 2**.

**Team**: Codeinit  
**Institution**: GRAPHIC ERA HILL UNIVERSITY  
**Members**: Mihir Swarnkar, Taniya Taragi, Tarun Pathak  
**Round 1 Submission**: January 2026

---

## 📌 Round 2 Evidence Checklist
- `benchmark_results.json` (20-run benchmarking)
- `benchmark_slide7.md` (slide-ready table)
- `output/carla_validation.json` (CARLA latency + response logs)
- `output/<Service>/traceability_matrix.csv` (ASPICE SWE.3)
- `output/metrics_summary.json` (Slide 9 metrics)

## 📄 License

This project is developed for the TATA ELXSI TELIPORT competition.

---

<p align="center">
  <strong>Built with ❤️ for the future of automotive software</strong>
</p>

<p align="center">
  <i>AUTOFORGE - Where AI meets Automotive Safety</i>
</p>
