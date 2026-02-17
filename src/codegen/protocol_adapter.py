"""
Protocol Adapter Generator

Generates protocol-specific configuration artifacts from requirement YAML.
Supports:
- SOME/IP configuration export
- Protocol Abstraction with SOME/IP code generation artifacts
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

    def generate_someip_abstraction_assets(self, requirement: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate Protocol Abstraction artifacts (code skeleton + mapping proof)
        for SOME/IP, while runtime validation can continue using REST transport.
        """
        config = self._generate_someip_config(requirement)
        svc = config["service"]
        methods = config.get("methods", [])
        events = config.get("events", [])
        service_name = str(svc.get("name") or "UnknownService")

        service_id = self._hex_or_default(svc.get("service_id"), "0x1001")
        instance_id = self._hex_or_default(svc.get("instance_id"), "0x0001")

        method_consts = "\n".join(
            f"static constexpr uint16_t {self._to_const_name(m.get('name', 'METHOD'))}_ID = {self._hex_or_default(m.get('id'), '0x0000')};"
            for m in methods
        ) or "static constexpr uint16_t GET_BATTERY_STATUS_ID = 0x0001;"

        event_consts = "\n".join(
            f"static constexpr uint16_t {self._to_const_name(e.get('name', 'EVENT'))}_ID = {self._hex_or_default(e.get('id'), '0x8000')};"
            for e in events
        ) or "static constexpr uint16_t BATTERY_WARNING_ID = 0x8001;"

        method_registration = "\n".join(
            (
                f"    app_->register_message_handler({service_id}, {instance_id}, "
                f"{self._hex_or_default(m.get('id'), '0x0000')}, "
                f"std::bind(&{service_name}Service::on_{m.get('name', 'method').lower()}, this, std::placeholders::_1));"
            )
            for m in methods
        ) or (
            f"    app_->register_message_handler({service_id}, {instance_id}, 0x0001, "
            f"std::bind(&{service_name}Service::on_getbatterystatus, this, std::placeholders::_1));"
        )

        handler_decls = "\n".join(
            f"    void on_{m.get('name', 'method').lower()}(const std::shared_ptr<vsomeip::message>& request);"
            for m in methods
        ) or "    void on_getbatterystatus(const std::shared_ptr<vsomeip::message>& request);"

        handler_defs = "\n\n".join(
            self._handler_def_template(service_name, m.get("name", "method"))
            for m in methods
        ) or self._handler_def_template(service_name, "GetBatteryStatus")

        method_id_rows = "\n".join(
            f"| `{m.get('name')}` | `{self._hex_or_default(m.get('id'), '0x0000')}` | `POST /bms/diagnostics` |"
            for m in methods
        ) or "| `GetBatteryStatus` | `0x0001` | `POST /bms/diagnostics` |"

        fields = [
            "vehicle_speed",
            "battery_soc",
            "battery_temperature",
            "tire_pressure_fl",
            "tire_pressure_fr",
            "tire_pressure_rl",
            "tire_pressure_rr",
        ]
        payload_rows = "\n".join(
            f"| `{f}` | `{f}` | same semantic signal |" for f in fields
        )

        vsomeip_config = {
            "unicast": "127.0.0.1",
            "applications": [{"name": f"{service_name}_app", "id": "0x1313"}],
            "services": [
                {
                    "service": service_id,
                    "instance": instance_id,
                    "unreliable": "30509",
                    "reliable": "30490",
                    "events": [self._hex_or_default(e.get("id"), "0x8000") for e in events],
                }
            ],
            "routing": f"{service_name}_app",
        }

        header = f"""#pragma once
#include <cstdint>
#include <memory>
#include <vsomeip/vsomeip.hpp>

class {service_name}Service {{
public:
    {service_name}Service();
    bool init();
    void start();
    void stop();

    static constexpr uint16_t SERVICE_ID = {service_id};
    static constexpr uint16_t INSTANCE_ID = {instance_id};
    {method_consts}
    {event_consts}

private:
    std::shared_ptr<vsomeip::application> app_;
    {handler_decls}
}};
"""

        server_cpp = f"""#include "vsomeip_service.hpp"
#include <iostream>

{service_name}Service::{service_name}Service() = default;

bool {service_name}Service::init() {{
    app_ = vsomeip::runtime::get()->create_application("{service_name}_app");
    if (!app_ || !app_->init()) return false;

{method_registration}
    app_->offer_service(SERVICE_ID, INSTANCE_ID);
    return true;
}}

void {service_name}Service::start() {{
    app_->start();
}}

void {service_name}Service::stop() {{
    if (app_) app_->stop();
}}

{handler_defs}
"""

        client_cpp = f"""#include <vsomeip/vsomeip.hpp>
#include <iostream>

int main() {{
    auto app = vsomeip::runtime::get()->create_application("{service_name}_client");
    if (!app || !app->init()) {{
        std::cerr << "Failed to init vsomeip client\\n";
        return 1;
    }}
    std::cout << "[ABSTRACTION] SOME/IP client skeleton ready for service "
              << "{service_name}" << "\\n";
    return 0;
}}
"""

        mapping_md = f"""# Protocol Abstraction with SOME/IP Code Generation

Service: `{service_name}`

This project validates business logic through REST during local development, and
generates SOME/IP code artifacts to map the same service contract into automotive
middleware integration.

## Method Mapping

| Service Method | SOME/IP Method ID | Current Validation Transport |
|---|---:|---|
{method_id_rows}

## Payload Mapping

| REST Field | SOME/IP Payload Field | Notes |
|---|---|---|
{payload_rows}

## Scope Clarification

- This is **Protocol Abstraction with SOME/IP Code Generation**, not a full vehicle-bus deployment.
- Generated artifacts: `vsomeip_config.json`, `vsomeip_service.hpp`, `vsomeip_service.cpp`, `vsomeip_client.cpp`.
- Existing REST validation path remains unchanged for deterministic CI/local testing.
"""

        return {
            "vsomeip_config.json": json.dumps(vsomeip_config, indent=2),
            "vsomeip_service.hpp": header,
            "vsomeip_service.cpp": server_cpp,
            "vsomeip_client.cpp": client_cpp,
            "protocol_mapping.md": mapping_md,
        }

    @staticmethod
    def _hex_or_default(value: Any, default_hex: str) -> str:
        if value is None:
            return default_hex
        if isinstance(value, int):
            return hex(value)
        return str(value)

    @staticmethod
    def _to_const_name(name: str) -> str:
        return "".join(c if c.isalnum() else "_" for c in str(name)).upper()

    def _handler_def_template(self, service_name: str, method_name: str) -> str:
        lname = str(method_name).lower()
        return f"""void {service_name}Service::on_{lname}(const std::shared_ptr<vsomeip::message>& request) {{
    // Protocol Abstraction skeleton:
    // Map request payload to domain DTO, call existing service logic, return response.
    auto response = vsomeip::runtime::get()->create_response(request);
    // TODO: serialize BMS diagnostics response payload here.
    app_->send(response);
}}"""

    def save(self, config: Dict[str, Any], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(config, indent=2))
        return output_path

    def save_assets(self, assets: Dict[str, str], output_dir: Path) -> List[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        written: List[Path] = []
        for name, content in assets.items():
            path = output_dir / name
            path.write_text(content)
            written.append(path)
        return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate protocol adapter config from requirement YAML")
    parser.add_argument("--requirement", "-r", required=True, help="Path to requirement YAML")
    parser.add_argument("--output", "-o", default="someip_service.json", help="Output JSON path")
    parser.add_argument(
        "--abstraction-dir",
        default="",
        help="Optional output directory for SOME/IP code generation artifacts",
    )
    args = parser.parse_args()

    requirement_path = Path(args.requirement)
    if not requirement_path.exists():
        raise FileNotFoundError(f"Requirement file not found: {requirement_path}")

    requirement = yaml.safe_load(requirement_path.read_text())
    generator = ProtocolAdapterGenerator()
    config = generator.generate(requirement)
    output_path = generator.save(config, Path(args.output))
    print(f"Saved protocol config: {output_path}")

    if args.abstraction_dir and config.get("protocol") == "someip":
        assets = generator.generate_someip_abstraction_assets(requirement)
        written = generator.save_assets(assets, Path(args.abstraction_dir))
        for p in written:
            print(f"Saved abstraction artifact: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
