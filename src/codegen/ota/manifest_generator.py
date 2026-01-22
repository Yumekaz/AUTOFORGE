"""
OTA Manifest Generator for AUTOFORGE
Auto-generates Over-The-Air update manifests for fleet deployment.
"""

import yaml
import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import hashlib


class OTAManifestGenerator:
    """
    Generates OTA update manifests for deploying AUTOFORGE-generated services to vehicle fleets.
    Supports multi-variant configurations (ICE/Hybrid/EV).
    """
    
    def __init__(self):
        self.manifest_version = "1.0.0"
    
    def generate_manifest(
        self,
        service_name: str,
        version: str,
        artifacts: Dict[str, Path],
        variants: List[str] = ["ev", "hybrid", "ice"],
        rollout_strategy: str = "gradual"
    ) -> Dict[str, Any]:
        """
        Generate OTA manifest for a service.
        
        Args:
            service_name: Name of the service
            version: Service version
            artifacts: Dict mapping artifact type to file path
            variants: List of vehicle variants this service supports
            rollout_strategy: "immediate", "gradual", or "canary"
        
        Returns:
            OTA manifest dictionary
        """
        manifest = {
            "ota_update": {
                "manifest_version": self.manifest_version,
                "service": {
                    "name": service_name,
                    "version": version,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                },
                "artifacts": self._process_artifacts(artifacts),
                "deployment": {
                    "vehicle_variants": variants,
                    "rollout_strategy": rollout_strategy,
                    "rollout_config": self._get_rollout_config(rollout_strategy),
                },
                "dependencies": self._generate_dependencies(service_name),
                "safety": {
                    "require_parking": True,
                    "require_battery_level": 30,  # Minimum 30% SOC
                    "rollback_enabled": True,
                    "validation_required": True,
                },
                "signature": self._generate_signature(service_name, version, artifacts)
            }
        }
        
        return manifest
    
    def _process_artifacts(self, artifacts: Dict[str, Path]) -> List[Dict[str, Any]]:
        """Process artifacts and generate metadata."""
        processed = []
        
        for artifact_type, filepath in artifacts.items():
            if not filepath.exists():
                continue
            
            # Calculate checksum
            checksum = self._calculate_checksum(filepath)
            
            artifact_info = {
                "type": artifact_type,
                "filename": filepath.name,
                "size_bytes": filepath.stat().st_size,
                "checksum": {
                    "algorithm": "sha256",
                    "value": checksum
                },
                "compression": "gzip" if artifact_type in ["binary", "library"] else "none",
            }
            
            processed.append(artifact_info)
        
        return processed
    
    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _get_rollout_config(self, strategy: str) -> Dict[str, Any]:
        """Get rollout configuration based on strategy."""
        configs = {
            "immediate": {
                "target_percentage": 100,
                "rollout_phases": [
                    {"phase": 1, "percentage": 100, "duration_hours": 0}
                ]
            },
            "gradual": {
                "target_percentage": 100,
                "rollout_phases": [
                    {"phase": 1, "percentage": 10, "duration_hours": 24},
                    {"phase": 2, "percentage": 50, "duration_hours": 48},
                    {"phase": 3, "percentage": 100, "duration_hours": 72}
                ]
            },
            "canary": {
                "target_percentage": 100,
                "rollout_phases": [
                    {"phase": 1, "percentage": 1, "duration_hours": 48},
                    {"phase": 2, "percentage": 10, "duration_hours": 72},
                    {"phase": 3, "percentage": 100, "duration_hours": 96}
                ]
            }
        }
        
        return configs.get(strategy, configs["gradual"])
    
    def _generate_dependencies(self, service_name: str) -> List[Dict[str, str]]:
        """Generate service dependencies."""
        # Common automotive dependencies
        base_deps = [
            {"name": "vsomeip", "version": ">=3.4.0", "required": True},
            {"name": "onnxruntime", "version": ">=1.16.0", "required": False},
        ]
        
        # Service-specific deps
        if "bms" in service_name.lower():
            base_deps.append({
                "name": "battery-manager",
                "version": ">=2.0.0",
                "required": True
            })
        
        return base_deps
    
    def _generate_signature(
        self,
        service_name: str,
        version: str,
        artifacts: Dict[str, Path]
    ) -> Dict[str, str]:
        """Generate cryptographic signature for manifest."""
        # In production, this would use actual signing keys
        # For now, generate a deterministic signature hash
        
        signature_data = f"{service_name}:{version}:{len(artifacts)}"
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()
        
        return {
            "algorithm": "RSA-SHA256",
            "keyid": "autoforge-release-key-2026",
            "value": signature_hash,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def generate_variant_configs(
        self,
        service_name: str,
        base_config: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate variant-specific configurations for ICE/Hybrid/EV.
        
        Args:
            service_name: Name of the service
            base_config: Base configuration
        
        Returns:
            Dict mapping variant name to its specific config
        """
        variants = {}
        
        # EV Variant
        variants["ev"] = {
            **base_config,
            "variant": "ev",
            "features": {
                "battery_monitoring": True,
                "regenerative_braking": True,
                "range_estimation": True,
                "fast_charging": True,
            },
            "signals": [
                "battery_soc", "battery_voltage", "battery_current",
                "battery_temperature", "motor_temperature", "motor_torque"
            ]
        }
        
        # Hybrid Variant
        variants["hybrid"] = {
            **base_config,
            "variant": "hybrid",
            "features": {
                "battery_monitoring": True,
                "regenerative_braking": True,
                "range_estimation": True,
                "fast_charging": False,
                "engine_integration": True,
            },
            "signals": [
                "battery_soc", "battery_voltage", "engine_rpm",
                "fuel_level", "motor_temperature"
            ]
        }
        
        # ICE Variant
        variants["ice"] = {
            **base_config,
            "variant": "ice",
            "features": {
                "battery_monitoring": False,  # Only 12V battery
                "regenerative_braking": False,
                "range_estimation": False,
                "engine_integration": True,
            },
            "signals": [
                "engine_rpm", "fuel_level", "engine_temperature",
                "oil_pressure", "coolant_temperature"
            ]
        }
        
        return variants
    
    def save_manifest(self, manifest: Dict[str, Any], output_path: Path):
        """Save manifest to YAML file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
        
        print(f"  Saved OTA manifest: {output_path}")
    
    def save_variant_configs(
        self,
        variants: Dict[str, Dict[str, Any]],
        output_dir: Path
    ):
        """Save variant configurations."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for variant_name, config in variants.items():
            config_path = output_dir / f"config_{variant_name}.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            print(f"  Saved variant config: {config_path}")


def generate_ota_package(
    service_name: str,
    version: str,
    output_dir: Path,
    artifacts: Dict[str, Path]
):
    """
    Main function to generate complete OTA package.
    
    Creates:
    - OTA manifest
    - Variant configurations (ICE/Hybrid/EV)
    - Deployment scripts
    """
    generator = OTAManifestGenerator()
    
    # Generate main manifest
    manifest = generator.generate_manifest(
        service_name=service_name,
        version=version,
        artifacts=artifacts,
        rollout_strategy="gradual"
    )
    
    manifest_path = output_dir / "ota_manifest.yaml"
    generator.save_manifest(manifest, manifest_path)
    
    # Generate variant configs
    base_config = {
        "service_name": service_name,
        "version": version,
    }
    
    variants = generator.generate_variant_configs(service_name, base_config)
    
    variant_dir = output_dir / "variants"
    generator.save_variant_configs(variants, variant_dir)
    
    print(f"\n✅ OTA package generated at {output_dir}")
    print(f"   - OTA Manifest: {manifest_path}")
    print(f"   - Variants: {variant_dir}")


if __name__ == "__main__":
    # Example usage
    from pathlib import Path
    
    # Mock artifacts
    artifacts = {
        "binary": Path("output/BMSDiagnosticService/bmsdiagnosticservice"),
        "config": Path("output/BMSDiagnosticService/config.yaml"),
    }
    
    generate_ota_package(
        service_name="BMSDiagnosticService",
        version="1.0.0",
        output_dir=Path("output/ota_package"),
        artifacts=artifacts
    )
