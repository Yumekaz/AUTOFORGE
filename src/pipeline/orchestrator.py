"""
AUTOFORGE Pipeline Orchestrator
Test-First GenAI Pipeline for Automotive SDV Code Generation
"""

import os
import json
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from llm.client import get_client
from llm.adversarial_client import get_auditor, get_architect
from llm.prompts import SYSTEM_PROMPT, TEST_GENERATION_PROMPT, CODE_GENERATION_PROMPT
from pipeline.validation_gate import get_validation_gate
from pipeline.traceability import TraceabilityMatrix
from pipeline.audit_logger import AuditLogger
from pipeline.onnx_wrapper_generator import ONNXWrapperGenerator
from pipeline.metrics_generator import generate_metrics
from codegen.protocol_adapter import ProtocolAdapterGenerator


class PipelinePhase(Enum):
    PARSE = "parse"
    TEST_GEN = "test_generation"
    CODE_GEN = "code_generation"
    VALIDATE = "validation"
    PACKAGE = "packaging"


@dataclass
class PipelineResult:
    """Result of a pipeline run."""
    success: bool
    requirement_id: str
    phases_completed: List[PipelinePhase]
    test_code: Optional[str] = None
    generated_code: Optional[str] = None
    validation_passed: bool = False
    retry_count: int = 0
    errors: List[str] = field(default_factory=list)
    trace_id: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.trace_id:
            self.trace_id = f"TRACE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class Pipeline:
    """
    AUTOFORGE Pipeline: Test-First GenAI with ADVERSARIAL GOVERNANCE
    
    The core insight: GenAI cannot check its own work.
    We use TWO SEPARATE AGENTS that work against each other:
    
    1. THE AUDITOR: Skeptical, strict - generates tests & validates
    2. THE ARCHITECT: Creative, implementation-focused - writes code
    
    This adversarial approach ensures code quality without hallucinations.
    """
    
    def __init__(
        self,
        llm_provider: str = "gemini",
        max_retries: int = 3,
        output_dir: str = "output",
    ):
        # CRITICAL: Use SEPARATE agents for adversarial governance
        self.auditor = get_auditor(llm_provider)
        self.architect = get_architect(llm_provider)
        self.llm_provider = llm_provider
        
        self.max_retries = max_retries
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def run(self, requirement_path: str) -> PipelineResult:
        """
        Run the complete pipeline for a requirement.
        
        Phases:
        1. PARSE: Load and validate requirement YAML
        2. TEST_GEN: Generate tests FIRST (the key insight!)
        3. CODE_GEN: Generate implementation to pass tests
        4. VALIDATE: Run tests, check compilation, MISRA
        5. PACKAGE: Bundle outputs with traceability
        """
        result = PipelineResult(
            success=False,
            requirement_id="",
            phases_completed=[],
        )
        audit = AuditLogger(service_name="unknown")
        
        self._print_section("AUTOFORGE PIPELINE START")
        self._print_kv("Requirement", requirement_path)

        # Phase 1: Parse
        self._print_step("PHASE 1", "INPUT", f"Parsing requirement: {requirement_path}")
        try:
            phase = audit.start_phase(1, "PARSE")
            requirement = self._parse_requirement(requirement_path)
            result.requirement_id = requirement.get("service", {}).get("name", "unknown")
            audit.service_name = result.requirement_id
            result.phases_completed.append(PipelinePhase.PARSE)
            self._print_kv("Service", result.requirement_id)
            audit.end_phase(phase, "SUCCESS", {
                "requirement_path": requirement_path,
                "service_name": result.requirement_id
            })
        except Exception as e:
            result.errors.append(f"Parse error: {str(e)}")
            if 'phase' in locals():
                audit.end_phase(phase, "FAILED", {"error": str(e)})
            self._save_audit(audit, result.requirement_id)
            return result
            
        # Phase 2: Generate Tests FIRST
        self._print_step("PHASE 2", "AUDITOR", f"Generating tests for: {result.requirement_id}")
        try:
            phase = audit.start_phase(2, "TEST_GENERATION")
            test_code = self._generate_tests(requirement)
            result.test_code = test_code
            result.phases_completed.append(PipelinePhase.TEST_GEN)
            self._save_output(result.requirement_id, "tests.py", test_code)
            audit.end_phase(phase, "SUCCESS", {
                "test_lines": len(test_code.splitlines())
            })
        except Exception as e:
            result.errors.append(f"Test generation error: {str(e)}")
            if 'phase' in locals():
                audit.end_phase(phase, "FAILED", {"error": str(e)})
            self._save_audit(audit, result.requirement_id)
            return result
            
        # Phase 3: Generate Code (with retry loop)
        self._print_step("PHASE 3", "ARCHITECT", "Generating implementation...")
        language = requirement.get("service", {}).get("language", "python")
        
        for attempt in range(self.max_retries):
            result.retry_count = attempt + 1
            self._print_attempt(attempt + 1, self.max_retries)
            
            try:
                phase = audit.start_phase(3, "CODE_GENERATION")
                generated_code = self._generate_code(requirement, test_code, language)
                result.generated_code = generated_code
                result.phases_completed.append(PipelinePhase.CODE_GEN)
                audit.end_phase(phase, "SUCCESS", {
                    "language": language,
                    "code_lines": len(generated_code.splitlines()),
                    "attempt": attempt + 1,
                })
                
                # Phase 4: Validate with REAL tools (clang-tidy, pytest, etc.)
                self._print_step("PHASE 4", "VALIDATION GATE", "Running compile/test/static checks...")
                phase_val = audit.start_phase(4, "VALIDATION")
                validation_result = self._validate(generated_code, test_code, language)
                
                if validation_result["valid"]:
                    result.validation_passed = True
                    result.phases_completed.append(PipelinePhase.VALIDATE)
                    self._print_status("VALIDATION", "PASS")
                    audit.end_phase(phase_val, "SUCCESS", {
                        "issues": validation_result.get("issues", []),
                        "misra": validation_result.get("misra_compliance", {}),
                        "asil_d": validation_result.get("asil_d_compliance", {}),
                        "static_analysis": validation_result.get("static_analysis", {}),
                    })
                    break
                else:
                    self._print_status("VALIDATION", "FAIL")
                    self._print_issues(validation_result.get("issues", []))
                    audit.end_phase(phase_val, "FAILED", {
                        "issues": validation_result.get("issues", []),
                        "misra": validation_result.get("misra_compliance", {}),
                        "asil_d": validation_result.get("asil_d_compliance", {}),
                        "static_analysis": validation_result.get("static_analysis", {}),
                    })
                    # Feed errors back for retry
                    test_code = self._enhance_tests_with_errors(test_code, validation_result["issues"])
                    
            except Exception as e:
                result.errors.append(f"Attempt {attempt + 1} error: {str(e)}")
                if 'phase' in locals():
                    audit.end_phase(phase, "FAILED", {"error": str(e), "attempt": attempt + 1})
                
        # Phase 5: Package
        if result.validation_passed:
            self._print_step("PHASE 5", "PACKAGER", "Packaging outputs and evidence...")
            phase = audit.start_phase(5, "PACKAGING")
            self._package_outputs(result, requirement, language)
            result.phases_completed.append(PipelinePhase.PACKAGE)
            result.success = True
            audit.end_phase(phase, "SUCCESS")
            
        audit.finalize(
            final_status="ACCEPTED" if result.success else "REJECTED",
            total_attempts=result.retry_count,
            compliance_summary={
                "validation_passed": result.validation_passed,
            },
            outputs={
                "trace": f"output/{result.requirement_id}/trace.yaml",
                "audit_report": f"output/{result.requirement_id}/audit_report.json",
            },
            requirement_traceability={
                "requirement_id": requirement.get("traceability", {}).get("requirement_id", "N/A"),
                "source_document": requirement_path,
            },
        )
        self._save_audit(audit, result.requirement_id)

        self._print_section("AUTOFORGE PIPELINE END")
        self._print_status("RESULT", "SUCCESS" if result.success else "FAILED")
        return result
    
    def _parse_requirement(self, path: str) -> Dict[str, Any]:
        """Load and validate requirement YAML."""
        with open(path, 'r') as f:
            req = yaml.safe_load(f)
            
        # Basic validation
        if "service" not in req:
            raise ValueError("Requirement must have 'service' section")
        if "name" not in req["service"]:
            raise ValueError("Service must have 'name'")
            
        return req
    
    def _generate_tests(self, requirement: Dict[str, Any]) -> str:
        """
        Generate tests FIRST using the AUDITOR agent.
        The Auditor is skeptical and creates comprehensive, strict tests.
        """
        prompt = TEST_GENERATION_PROMPT.format(
            requirement_yaml=yaml.dump(requirement)
        )
        
        # Use AUDITOR agent (not the same LLM as code generation!)
        response = self.auditor.generate(prompt, system_prompt=SYSTEM_PROMPT)
        return self._extract_code(response)
    
    def _generate_code(
        self, 
        requirement: Dict[str, Any], 
        test_code: str,
        language: str
    ) -> str:
        """
        Generate implementation using the ARCHITECT agent.
        The Architect must write code that passes ALL tests from the Auditor.
        """
        protocol = requirement.get("service", {}).get("protocol", "none")
        
        prompt = CODE_GENERATION_PROMPT.format(
            requirement_yaml=yaml.dump(requirement),
            test_code=test_code,
            language=language,
            protocol=protocol,
        )
        
        # Use ARCHITECT agent (different from the Auditor!)
        response = self.architect.generate(prompt, system_prompt=SYSTEM_PROMPT)
        return self._extract_code(response)
    
    def _validate(self, code: str, test_code: str, language: str) -> Dict[str, Any]:
        """
        Validate generated code using the real ValidationGate.
        This runs actual static analysis tools, not just basic checks.
        """
        gate = get_validation_gate()
        return gate.validate(code, test_code, language)
    
    def _enhance_tests_with_errors(self, test_code: str, errors: List[str]) -> str:
        """Add error context to tests for retry."""
        error_comment = "\n".join(f"# ERROR FROM PREVIOUS ATTEMPT: {e}" for e in errors)
        return f"{error_comment}\n\n{test_code}"
    
    def _package_outputs(
        self, 
        result: PipelineResult, 
        requirement: Dict[str, Any],
        language: str
    ):
        """Save all outputs with traceability and OTA manifests."""
        service_name = result.requirement_id
        
        # Save implementation
        language_key = (language or "").lower()
        ext = {"python": "py", "cpp": "cpp", "rust": "rs", "kotlin": "kt", "java": "java"}.get(language_key, "txt")
        impl_file = f"{service_name.lower()}.{ext}"
        self._save_output(service_name, impl_file, result.generated_code)

        # Optional Java companion generation for Kotlin services.
        if language_key == "kotlin" and requirement.get("service", {}).get("generate_java_companion", False):
            try:
                java_code = self._generate_code(requirement, result.test_code or "", "java")
                self._save_output(service_name, f"{service_name}.java", java_code)
            except Exception as e:
                print(f"  Warning: Java companion generation skipped: {e}")
        
        # Save traceability
        trace = {
            "trace_id": result.trace_id,
            "timestamp": result.timestamp,
            "requirement_id": requirement.get("traceability", {}).get("requirement_id", "N/A"),
            "aspice_reference": requirement.get("traceability", {}).get("aspice_reference", "N/A"),
            "phases_completed": [p.value for p in result.phases_completed],
            "retry_count": result.retry_count,
            "validation_passed": result.validation_passed,
        }
        self._save_output(service_name, "trace.yaml", yaml.dump(trace))

        # Generate ASPICE traceability matrix
        matrix = TraceabilityMatrix()
        rows = matrix.build(requirement, result.test_code or "", result.generated_code or "")
        service_dir = self.output_dir / service_name
        matrix.save_csv(rows, service_dir / "traceability_matrix.csv")
        matrix.save_yaml(rows, service_dir / "traceability_matrix.yaml")
        
        # Generate OTA manifest and variant configs
        print(f"[PHASE 5.1] Generating OTA manifests...")
        self._generate_ota_package(service_name, requirement)

        # Generate protocol adapter artifact (e.g., SOME/IP config JSON)
        protocol_gen = ProtocolAdapterGenerator()
        protocol_config = protocol_gen.generate(requirement)
        protocol_name = requirement.get("service", {}).get("protocol", "generic").lower()
        protocol_filename = "someip_service.json" if protocol_name == "someip" else f"{protocol_name}_service.json"
        self._save_output(service_name, protocol_filename, json.dumps(protocol_config, indent=2))

        if protocol_name == "someip":
            abstraction_assets = protocol_gen.generate_someip_abstraction_assets(requirement)
            abstraction_dir = self.output_dir / service_name / "protocol_abstraction"
            protocol_gen.save_assets(abstraction_assets, abstraction_dir)
            print(f"  Saved protocol abstraction assets: {abstraction_dir}")

        # CARLA integration config (service endpoint)
        self._save_output(service_name, "carla_service_config.yaml", yaml.dump({
            "service_url": f"http://{service_name.lower()}:30509",
            "notes": "Used by integrations/carla_bridge/service_client.py",
        }))

        # Generate ONNX wrapper if ML block present
        if requirement.get("ml"):
            ml_cfg = requirement.get("ml", {})
            # Optional supervised training path (CPU-compatible) for ONNX artifact generation.
            if ml_cfg.get("train_model", False):
                try:
                    from ml.train import train_and_export
                    csv_path = ml_cfg.get("training_csv", "")
                    csv_input = Path(csv_path) if csv_path else None
                    model_output = Path(ml_cfg.get("model_path", "models/tire_failure.onnx"))
                    train_and_export(csv_input, model_output)
                except Exception as e:
                    print(f"  Warning: ML training/export skipped: {e}")

            print(f"[PHASE 5.2] Generating ONNX wrapper...")
            wrapper_gen = ONNXWrapperGenerator(llm_provider=self.llm_provider)
            wrapper_code = wrapper_gen.generate(requirement)
            self._save_output(service_name, "onnx_wrapper.hpp", wrapper_code)

        # Generate metrics summary artifact for slides
        metrics_path = self.output_dir / "metrics_summary.json"
        generate_metrics(metrics_path)

    def _print_section(self, title: str):
        print(f"\n{'=' * 72}")
        print(f"{title}")
        print(f"{'=' * 72}")

    def _print_step(self, phase: str, owner: str, message: str):
        print(f"[{phase}] [{owner}] {message}")

    def _print_attempt(self, current: int, total: int):
        print(f"  - Attempt {current}/{total}")

    def _print_status(self, label: str, status: str):
        print(f"  [{label}] {status}")

    def _print_kv(self, key: str, value: str):
        print(f"{key}: {value}")

    def _print_issues(self, issues: List[str]):
        if not issues:
            return
        print("  Issues:")
        for issue in issues:
            print(f"    - {issue}")
        
    def _save_output(self, service_name: str, filename: str, content: str):
        """Save output file."""
        service_dir = self.output_dir / service_name
        service_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = service_dir / filename
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  Saved: {filepath}")

    def _save_audit(self, audit: AuditLogger, service_name: str):
        if not service_name:
            return
        service_dir = self.output_dir / service_name
        audit_path = service_dir / "audit_report.json"
        audit.save(audit_path)
        
    def _extract_code(self, response: str) -> str:
        """Extract code from LLM response (handles markdown code blocks)."""
        # Remove markdown code blocks if present
        if "```" in response:
            lines = response.split("\n")
            code_lines = []
            in_code_block = False
            
            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    code_lines.append(line)
                    
            return "\n".join(code_lines)
        
        return response
    
    def _generate_ota_package(self, service_name: str, requirement: Dict[str, Any]):
        """Generate OTA manifest and variant configurations."""
        try:
            from codegen.ota.manifest_generator import OTAManifestGenerator
            
            generator = OTAManifestGenerator()
            service_dir = self.output_dir / service_name
            
            # Collect artifacts
            artifacts = {}
            for file in service_dir.glob("*"):
                if file.is_file() and file.suffix in ['.py', '.cpp', '.rs', '.kt', '.java']:
                    artifacts["binary"] = file
                elif file.name == "trace.yaml":
                    artifacts["trace"] = file
            
            # Generate OTA manifest
            manifest = generator.generate_manifest(
                service_name=service_name,
                version="1.0.0",
                artifacts=artifacts,
                rollout_strategy="gradual"
            )
            
            manifest_path = service_dir / "ota_manifest.yaml"
            generator.save_manifest(manifest, manifest_path)
            
            # Generate variant configs
            base_config = {
                "service_name": service_name,
                "version": "1.0.0",
            }
            variants = generator.generate_variant_configs(service_name, base_config)
            variant_dir = service_dir / "variants"
            generator.save_variant_configs(variants, variant_dir)
            
            print(f"  OTA package generated with {len(variants)} variants")
            
        except ImportError as e:
            print(f"  Warning: Could not generate OTA package: {e}")
        except Exception as e:
            print(f"  Warning: OTA generation failed: {e}")
