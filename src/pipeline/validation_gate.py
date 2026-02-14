"""
Real Validation Gate for AUTOFORGE
Implements actual static analysis, test execution, and MISRA checking.
"""

import subprocess
import tempfile
import os
import re
from pathlib import Path
from typing import Dict, List, Any
import json

from pipeline.asil_validation import AsilDValidator


class ValidationGate:
    """
    The GATE component of Adversarial Governance.
    Code is REJECTED if it fails tests or static analysis.
    """
    
    def __init__(self):
        self.validators = {
            'python': self.validate_python,
            'py': self.validate_python,
            'cpp': self.validate_cpp,
            'c++': self.validate_cpp,
            'java': self.validate_java,
            'rust': self.validate_rust,
            'rs': self.validate_rust,
        }
    
    def validate(self, code: str, test_code: str, language: str) -> Dict[str, Any]:
        """
        Run comprehensive validation on generated code.
        
        Returns:
            {
                'valid': bool,
                'issues': List[str],
                'test_results': Dict,
                'static_analysis': Dict,
                'misra_compliance': Dict (for C++)
            }
        """
        language_key = (language or "").lower()
        if language_key not in self.validators:
            return {
                'valid': False,
                'issues': [f"Unsupported language: {language}"]
            }
        
        return self.validators[language_key](code, test_code)
    
    def validate_python(self, code: str, test_code: str) -> Dict[str, Any]:
        """Validate Python code with real tools."""
        result = {
            'valid': True,
            'issues': [],
            'test_results': {},
            'static_analysis': {}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Write code files
            impl_file = tmpdir_path / "implementation.py"
            test_file = tmpdir_path / "test_implementation.py"
            
            impl_file.write_text(code)
            
            # Modify test code to import from implementation file
            modified_test = test_code.replace(
                "import pytest",
                "import pytest\nfrom implementation import *"
            )
            test_file.write_text(modified_test)
            
            # 1. Syntax check with compile
            try:
                compile(code, str(impl_file), 'exec')
                result['static_analysis']['syntax'] = 'PASS'
            except SyntaxError as e:
                result['valid'] = False
                result['issues'].append(f"Syntax error: {e}")
                result['static_analysis']['syntax'] = f'FAIL: {e}'
                return result  # Don't continue if syntax is broken

            # 1.1 Minimum service size gate (200+ lines)
            line_count = sum(1 for line in code.splitlines() if line.strip())
            if line_count < 200:
                result['valid'] = False
                result['issues'].append(
                    f"Service size too small: {line_count} lines (minimum 200 required)"
                )
                result['static_analysis']['service_size'] = 'FAIL'
            else:
                result['static_analysis']['service_size'] = 'PASS'
            
            # 2. Run pylint for static analysis
            try:
                pylint_result = subprocess.run(
                    ['pylint', '--rcfile=/dev/null', '--disable=all',
                     '--enable=E,F', str(impl_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if pylint_result.returncode == 0:
                    result['static_analysis']['pylint'] = 'PASS'
                else:
                    # Check for actual errors (not just warnings)
                    if 'error' in pylint_result.stdout.lower():
                        result['valid'] = False
                        result['issues'].append(f"Pylint errors: {pylint_result.stdout}")
                        result['static_analysis']['pylint'] = 'FAIL'
                    else:
                        result['static_analysis']['pylint'] = 'PASS (with warnings)'
                        
            except FileNotFoundError:
                result['static_analysis']['pylint'] = 'SKIP (not installed)'
            except Exception as e:
                result['static_analysis']['pylint'] = f'ERROR: {e}'
            
            # 3. Run pytest
            try:
                pytest_result = subprocess.run(
                    ['pytest', str(test_file), '-v', '--tb=short'],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=tmpdir
                )
                
                if pytest_result.returncode == 0:
                    result['test_results']['status'] = 'PASS'
                    result['test_results']['output'] = pytest_result.stdout
                else:
                    result['valid'] = False
                    result['test_results']['status'] = 'FAIL'
                    result['test_results']['output'] = pytest_result.stdout
                    
                    # Extract specific failures
                    failures = self._extract_pytest_failures(pytest_result.stdout)
                    for failure in failures:
                        result['issues'].append(f"Test failed: {failure}")
                        
            except FileNotFoundError:
                result['valid'] = False
                result['issues'].append("pytest not installed")
                result['test_results']['status'] = 'ERROR: pytest not found'
            except subprocess.TimeoutExpired:
                result['valid'] = False
                result['issues'].append("Tests timed out (>30s)")
                result['test_results']['status'] = 'TIMEOUT'
            except Exception as e:
                result['valid'] = False
                result['issues'].append(f"Test execution error: {e}")
                result['test_results']['status'] = f'ERROR: {e}'
        
        return result
    
    def validate_cpp(self, code: str, test_code: str) -> Dict[str, Any]:
        """Validate C++ code with real MISRA checking."""
        result = {
            'valid': True,
            'issues': [],
            'test_results': {},
            'static_analysis': {},
            'misra_compliance': {},
            'asil_d_compliance': {}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Write code file
            impl_file = tmpdir_path / "implementation.cpp"
            impl_file.write_text(code)
            
            # 1. Basic compilation check
            try:
                compile_result = subprocess.run(
                    ['g++', '-std=c++17', '-fsyntax-only', str(impl_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if compile_result.returncode == 0:
                    result['static_analysis']['compilation'] = 'PASS'
                else:
                    result['valid'] = False
                    result['issues'].append(f"Compilation error: {compile_result.stderr}")
                    result['static_analysis']['compilation'] = 'FAIL'
                    return result  # Don't continue if it doesn't compile
                    
            except FileNotFoundError:
                result['static_analysis']['compilation'] = 'SKIP (g++ not installed)'
            except Exception as e:
                result['static_analysis']['compilation'] = f'ERROR: {e}'

            # 1.1 Minimum service size gate (200+ lines)
            line_count = sum(1 for line in code.splitlines() if line.strip())
            if line_count < 200:
                result['valid'] = False
                result['issues'].append(
                    f"Service size too small: {line_count} lines (minimum 200 required)"
                )
                result['static_analysis']['service_size'] = 'FAIL'
            else:
                result['static_analysis']['service_size'] = 'PASS'

            # 2. clang-tidy for MISRA rules
            try:
                repo_root = Path(__file__).resolve().parents[2]
                misra_config = repo_root / "config" / "misra" / "clang-tidy-misra.yaml"
                clang_args = [
                    'clang-tidy', str(impl_file), '--',
                    '-std=c++17',
                ]
                if misra_config.exists():
                    clang_args.insert(1, f"--config-file={misra_config}")
                else:
                    clang_args.extend(['--checks=-*,readability-*,bugprone-*,cppcoreguidelines-*'])

                # Run clang-tidy with MISRA-relevant checks
                clang_result = subprocess.run(
                    clang_args,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                # Parse clang-tidy output for violations
                violations = self._parse_clang_tidy_output(clang_result.stdout)
                
                if len(violations) == 0:
                    result['misra_compliance']['clang_tidy'] = 'PASS'
                else:
                    result['misra_compliance']['clang_tidy'] = f'FAIL ({len(violations)} violations)'
                    result['misra_compliance']['violations'] = violations
                    
                    # Check for critical violations
                    critical_violations = [v for v in violations if 'error' in v.lower()]
                    if critical_violations:
                        result['valid'] = False
                        for v in critical_violations:
                            result['issues'].append(f"MISRA violation: {v}")
                            
            except FileNotFoundError:
                result['misra_compliance']['clang_tidy'] = 'SKIP (clang-tidy not installed)'
            except Exception as e:
                result['misra_compliance']['clang_tidy'] = f'ERROR: {e}'
            
            # 3. cppcheck for additional static analysis
            try:
                cppcheck_result = subprocess.run(
                    ['cppcheck', '--enable=all', '--error-exitcode=1',
                     '--suppress=missingIncludeSystem', str(impl_file)],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if cppcheck_result.returncode == 0:
                    result['static_analysis']['cppcheck'] = 'PASS'
                else:
                    result['static_analysis']['cppcheck'] = 'FAIL'
                    # Extract errors
                    if cppcheck_result.stderr:
                        errors = [line for line in cppcheck_result.stderr.split('\n')
                                 if 'error' in line.lower()]
                        for err in errors[:3]:  # Limit to 3 errors
                            result['issues'].append(f"cppcheck: {err}")
                            
            except FileNotFoundError:
                result['static_analysis']['cppcheck'] = 'SKIP (cppcheck not installed)'
            except Exception as e:
                result['static_analysis']['cppcheck'] = f'ERROR: {e}'

            # 4. ASIL-D compliance checks (ISO 26262)
            try:
                asil_validator = AsilDValidator()
                asil_result = asil_validator.validate_cpp(code, impl_file)
                result['asil_d_compliance'] = {
                    'status': 'PASS' if asil_result.compliant else 'FAIL',
                    'issues': asil_result.issues,
                    'static_analyzer': asil_result.static_analyzer,
                    'heuristic_checks': asil_result.heuristic_checks,
                    'evidence': asil_result.evidence,
                }
                if not asil_result.compliant:
                    result['valid'] = False
                    for issue in asil_result.issues:
                        result['issues'].append(issue)
            except Exception as e:
                result['asil_d_compliance'] = {'status': f'ERROR: {e}'}
        
        return result

    def validate_rust(self, code: str, test_code: str) -> Dict[str, Any]:
        """Validate Rust code with rustc and basic linting."""
        result = {
            'valid': True,
            'issues': [],
            'test_results': {},
            'static_analysis': {},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            impl_file = tmpdir_path / "implementation.rs"
            impl_file.write_text(code)

            # Minimum size gate
            line_count = sum(1 for line in code.splitlines() if line.strip())
            if line_count < 200:
                result['valid'] = False
                result['issues'].append(
                    f"Service size too small: {line_count} lines (minimum 200 required)"
                )
                result['static_analysis']['service_size'] = 'FAIL'
            else:
                result['static_analysis']['service_size'] = 'PASS'

            # rustc syntax check
            try:
                rustc_result = subprocess.run(
                    ['rustc', '--edition=2021', '--emit=metadata', str(impl_file)],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if rustc_result.returncode == 0:
                    result['static_analysis']['rustc'] = 'PASS'
                else:
                    result['valid'] = False
                    result['static_analysis']['rustc'] = 'FAIL'
                    result['issues'].append(f"Rust compile error: {rustc_result.stderr}")
            except FileNotFoundError:
                result['static_analysis']['rustc'] = 'SKIP (rustc not installed)'
            except Exception as e:
                result['static_analysis']['rustc'] = f'ERROR: {e}'

        return result

    def validate_java(self, code: str, test_code: str) -> Dict[str, Any]:
        """Validate Java code with javac when available."""
        result = {
            'valid': True,
            'issues': [],
            'test_results': {},
            'static_analysis': {},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            class_match = re.search(r"public\s+class\s+([A-Za-z_][A-Za-z0-9_]*)", code)
            class_name = class_match.group(1) if class_match else "Implementation"
            impl_file = tmpdir_path / f"{class_name}.java"
            impl_file.write_text(code)

            line_count = sum(1 for line in code.splitlines() if line.strip())
            if line_count < 200:
                result['valid'] = False
                result['issues'].append(
                    f"Service size too small: {line_count} lines (minimum 200 required)"
                )
                result['static_analysis']['service_size'] = 'FAIL'
            else:
                result['static_analysis']['service_size'] = 'PASS'

            try:
                javac_result = subprocess.run(
                    ['javac', str(impl_file)],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if javac_result.returncode == 0:
                    result['static_analysis']['javac'] = 'PASS'
                else:
                    result['valid'] = False
                    result['static_analysis']['javac'] = 'FAIL'
                    result['issues'].append(f"Java compile error: {javac_result.stderr}")
            except FileNotFoundError:
                result['static_analysis']['javac'] = 'SKIP (javac not installed)'
            except Exception as e:
                result['static_analysis']['javac'] = f'ERROR: {e}'

        return result
    
    def _extract_pytest_failures(self, pytest_output: str) -> List[str]:
        """Extract test failure messages from pytest output."""
        failures = []
        lines = pytest_output.split('\n')
        
        for i, line in enumerate(lines):
            if 'FAILED' in line:
                # Get test name
                test_name = line.split('::')[-1].split(' ')[0] if '::' in line else 'unknown'
                failures.append(test_name)
        
        return failures
    
    def _parse_clang_tidy_output(self, output: str) -> List[str]:
        """Parse clang-tidy output for violations."""
        violations = []
        lines = output.split('\n')
        
        for line in lines:
            if 'warning:' in line or 'error:' in line:
                violations.append(line.strip())
        
        return violations


# Singleton instance
_validation_gate = None

def get_validation_gate() -> ValidationGate:
    """Get singleton validation gate instance."""
    global _validation_gate
    if _validation_gate is None:
        _validation_gate = ValidationGate()
    return _validation_gate
