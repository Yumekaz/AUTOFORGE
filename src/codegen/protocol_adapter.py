"""
Protocol Adapter Generator

Generates protocol-specific configuration artifacts from requirement YAML.
Currently supports SOME/IP configuration export.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import json
import argparse
import yaml


class ProtocolAdapterGenerator:
    """Generate protocol adapter artifacts."""

    def generate(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        service = requirement.get("service", {})
        protocol = service.get("protocol", "").lower()

        if protocol == "someip":
            return self._generate_someip_config(requirement)

        return {
            "protocol": protocol or "unknown",
            "service": service.get("name", "UnknownService"),
            "note": "No dedicated adapter template for this protocol",
        }

    def _generate_someip_config(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        service = requirement.get("service", {})
        interface = service.get("interface", {})
        methods = interface.get("methods", [])
        events = interface.get("events", [])

        method_list: List[Dict[str, Any]] = []
        for m in methods:
            method_list.append(
                {
                    "name": m.get("name"),
                    "id": m.get("id"),
                    "input": m.get("input", []),
                    "output": m.get("output", []),
                }
            )

        event_list: List[Dict[str, Any]] = []
        for e in events:
            event_list.append(
                {
                    "name": e.get("name"),
                    "id": e.get("id"),
                    "fields": e.get("fields", []),
                }
            )

        return {
            "protocol": "someip",
            "service": {
                "name": service.get("name"),
                "version": service.get("version", "1.0.0"),
                "service_id": interface.get("service_id"),
                "instance_id": interface.get("instance_id"),
            },
            "methods": method_list,
            "event_groups": [
                {
                    "name": "default_event_group",
                    "events": [e.get("name") for e in events if e.get("name")],
                }
            ],
            "events": event_list,
        }

    def save(self, config: Dict[str, Any], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(config, indent=2))
        return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate protocol adapter config from requirement YAML")
    parser.add_argument("--requirement", "-r", required=True, help="Path to requirement YAML")
    parser.add_argument("--output", "-o", default="someip_service.json", help="Output JSON path")
    args = parser.parse_args()

    requirement_path = Path(args.requirement)
    if not requirement_path.exists():
        raise FileNotFoundError(f"Requirement file not found: {requirement_path}")

    requirement = yaml.safe_load(requirement_path.read_text())
    generator = ProtocolAdapterGenerator()
    config = generator.generate(requirement)
    output_path = generator.save(config, Path(args.output))
    print(f"Saved protocol config: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
