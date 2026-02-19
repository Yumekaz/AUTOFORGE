# Protocol Abstraction with SOME/IP Code Generation

Service: `TirePressureDiagnosticService`

This project validates business logic through REST during local development, and
generates SOME/IP code artifacts to map the same service contract into automotive
middleware integration.

## Method Mapping

| Service Method | SOME/IP Method ID | Current Validation Transport |
|---|---:|---|
| `GetTireStatus` | `0x1` | `POST /bms/diagnostics` |

## Payload Mapping

| REST Field | SOME/IP Payload Field | Notes |
|---|---|---|
| `vehicle_speed` | `vehicle_speed` | same semantic signal |
| `battery_soc` | `battery_soc` | same semantic signal |
| `battery_temperature` | `battery_temperature` | same semantic signal |
| `tire_pressure_fl` | `tire_pressure_fl` | same semantic signal |
| `tire_pressure_fr` | `tire_pressure_fr` | same semantic signal |
| `tire_pressure_rl` | `tire_pressure_rl` | same semantic signal |
| `tire_pressure_rr` | `tire_pressure_rr` | same semantic signal |

## Scope Clarification

- This is **Protocol Abstraction with SOME/IP Code Generation**, not a full vehicle-bus deployment.
- Generated artifacts: `vsomeip_config.json`, `vsomeip_service.hpp`, `vsomeip_service.cpp`, `vsomeip_client.cpp`.
- Existing REST validation path remains unchanged for deterministic CI/local testing.
