# Protocol Abstraction with SOME/IP Code Generation

This repository uses a transport abstraction pattern:

- Runtime validation path: `REST` (deterministic local/CI flow)
- Automotive middleware path: `SOME/IP code generation artifacts` (vsomeip skeleton + mapping)

This is intentionally framed as **Protocol Abstraction with SOME/IP Code Generation**, not a full in-vehicle SOME/IP deployment.

## Why this approach

- Keeps business logic and validation loop unchanged.
- Produces auditable SOME/IP interface artifacts from requirement YAML.
- Demonstrates clear mapping from dev transport (REST) to automotive transport (SOME/IP).

## Generated artifacts

For a SOME/IP requirement, AUTOFORGE now produces:

- `output/<Service>/someip_service.json`
- `output/<Service>/protocol_abstraction/vsomeip_config.json`
- `output/<Service>/protocol_abstraction/vsomeip_service.hpp`
- `output/<Service>/protocol_abstraction/vsomeip_service.cpp`
- `output/<Service>/protocol_abstraction/vsomeip_client.cpp`
- `output/<Service>/protocol_abstraction/protocol_mapping.md`

## Command

```powershell
python src/codegen/protocol_adapter.py `
  --requirement input/requirements/bms_diagnostic.yaml `
  --output output/someip_service.json `
  --abstraction-dir output/someip_abstraction
```

## Transport adapters

Location:

- `integrations/transport/rest_transport.py`
- `integrations/transport/someip_transport.py`
- `integrations/transport/transport_interface.py`

Usage in bridge:

```powershell
python integrations/carla_bridge/carla_integration.py --mode replay --transport rest ...
python integrations/carla_bridge/carla_integration.py --mode replay --transport someip ...
```

`someip` mode is a placeholder contract in Python path and points to generated C++ artifacts for middleware binding.
