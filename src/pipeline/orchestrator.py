"""
AUTOFORGE Pipeline Orchestrator
Test-First GenAI Pipeline for Automotive SDV Code Generation
"""

import os
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
        
        # Phase 1: Parse
        print(f"[PHASE 1] Parsing requirement: {requirement_path}")
        try:
            requirement = self._parse_requirement(requirement_path)
            result.requirement_id = requirement.get("service", {}).get("name", "unknown")
            result.phases_completed.append(PipelinePhase.PARSE)
        except Exception as e:
            result.errors.append(f"Parse error: {str(e)}")
            return result
            
        # Phase 2: Generate Tests FIRST
        print(f"[PHASE 2] Generating tests for: {result.requirement_id}")
        try:
            test_code = self._generate_tests(requirement)
            result.test_code = test_code
            result.phases_completed.append(PipelinePhase.TEST_GEN)
            self._save_output(result.requirement_id, "tests.py", test_code)
        except Exception as e:
            result.errors.append(f"Test generation error: {str(e)}")
            return result
            
        # Phase 3: Generate Code (with retry loop)
        print(f"[PHASE 3] Generating implementation...")
        language = requirement.get("service", {}).get("language", "python")
        
        for attempt in range(self.max_retries):
            result.retry_count = attempt + 1
            print(f"  Attempt {attempt + 1}/{self.max_retries}")
            
            try:
                generated_code = self._generate_code(requirement, test_code, language)
                result.generated_code = generated_code
                result.phases_completed.append(PipelinePhase.CODE_GEN)
                
                # Phase 4: Validate with REAL tools (clang-tidy, pytest, etc.)
                print(f"[PHASE 4] Validating generated code...")
                validation_result = self._validate(generated_code, test_code, language)
                
                if validation_result["valid"]:
                    result.validation_passed = True
                    result.phases_completed.append(PipelinePhase.VALIDATE)
                    break
                else:
                    print(f"  Validation failed: {validation_result['issues']}")
                    # Feed errors back for retry
                    test_code = self._enhance_tests_with_errors(test_code, validation_result["issues"])
                    
            except Exception as e:
                result.errors.append(f"Attempt {attempt + 1} error: {str(e)}")
                
        # Phase 5: Package
        if result.validation_passed:
            print(f"[PHASE 5] Packaging outputs...")
            self._package_outputs(result, requirement, language)
            result.phases_completed.append(PipelinePhase.PACKAGE)
            result.success = True
            
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
        ext = {"python": "py", "cpp": "cpp", "rust": "rs", "kotlin": "kt"}.get(language, "txt")
        impl_file = f"{service_name.lower()}.{ext}"
        self._save_output(service_name, impl_file, result.generated_code)
        
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
        
        # Generate OTA manifest and variant configs
        print(f"[PHASE 5.1] Generating OTA manifests...")
        self._generate_ota_package(service_name, requirement)
        
    def _save_output(self, service_name: str, filename: str, content: str):
        """Save output file."""
        service_dir = self.output_dir / service_name
        service_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = service_dir / filename
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  Saved: {filepath}")
        
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
                if file.is_file() and file.suffix in ['.py', '.cpp', '.rs', '.kt']:
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
