#!/usr/bin/env python3
"""
AUTOFORGE CARLA Integration Bridge
Connects CARLA simulation to generated AUTOFORGE services for testing.

Modes:
- live: connect to CARLA and stream real-time simulated signals
- replay: replay recorded signals from JSON and validate service responses
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    import carla  # type: ignore
except ImportError:
    carla = None

# Add AUTOFORGE src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
sys.path.insert(0, os.path.dirname(__file__))

from service_client import ServiceClient
from carla_validation_logger import CarlaValidationLogger


class CARLABridge:
    """Bridge between CARLA simulation and AUTOFORGE services."""

    def __init__(self, carla_host: str = 'localhost', carla_port: int = 2000):
        if carla is None:
            raise RuntimeError(
                "carla package is not installed. Install the matching CARLA wheel from "
                "PythonAPI/carla/dist for live mode."
            )
        self.client = carla.Client(carla_host, carla_port)
        self.client.set_timeout(10.0)
        self.world = self.client.get_world()
        self.vehicle = None
        self.sensors = {}

    def spawn_test_vehicle(self):
        """Spawn a test vehicle with required sensors."""
        print("[CARLA] Spawning test vehicle...")

        blueprint_library = self.world.get_blueprint_library()
        vehicle_bp = blueprint_library.filter('vehicle.tesla.model3')[0]

        spawn_points = self.world.get_map().get_spawn_points()
        spawn_point = spawn_points[0] if spawn_points else carla.Transform()

        self.vehicle = self.world.spawn_actor(vehicle_bp, spawn_point)
        print(f"[CARLA] Vehicle spawned: {self.vehicle.type_id}")

        self._attach_sensors()

    def _attach_sensors(self):
        """Attach sensors if needed (placeholder)."""
        pass

    def get_vehicle_signals(self) -> Dict[str, Any]:
        """Extract vehicle signals required by AUTOFORGE services."""
        if not self.vehicle:
            return {}

        velocity = self.vehicle.get_velocity()
        control = self.vehicle.get_control()

        speed_mps = (velocity.x**2 + velocity.y**2 + velocity.z**2) ** 0.5
        speed_kmh = speed_mps * 3.6

        signals = {
            'vehicle_speed': speed_kmh,
            'gear_position': control.gear,
            'throttle_position': control.throttle * 100.0,
            'brake_pressure': control.brake * 200.0,
            'steering_angle': control.steer * 540.0,
            'battery_soc': self._simulate_battery_soc(),
            'battery_voltage': 400.0,
            'battery_current': control.throttle * 200.0 - control.brake * 100.0,
            'battery_temperature': self._simulate_battery_temp(),
            'estimated_range': self._estimate_range(),
            'tire_pressure_fl': 2.5,
            'tire_pressure_fr': 2.5,
            'tire_pressure_rl': 2.4,
            'tire_pressure_rr': 2.4,
            'motor_temperature': 50.0 + control.throttle * 30.0,
            'motor_torque': control.throttle * 350.0,
            'motor_power': (control.throttle * 350.0 * speed_mps) / 1000.0,
            'ambient_temperature': 25.0,
            'odometer': 12345.0,
        }

        return signals

    def _simulate_battery_soc(self) -> float:
        elapsed_time = self.world.get_snapshot().timestamp.elapsed_seconds
        return max(20.0, 100.0 - (elapsed_time / 100.0))

    def _simulate_battery_temp(self) -> float:
        if not self.vehicle:
            return 25.0
        control = self.vehicle.get_control()
        return 25.0 + control.throttle * 20.0

    def _estimate_range(self) -> float:
        soc = self._simulate_battery_soc()
        return soc * 4.0

    def stream_to_services(
        self,
        service_url: str = 'http://localhost:30509',
        log_path: str = 'output/carla_validation.json',
        transport: str = 'rest',
        max_samples: int = 0,
        rate_hz: float = 10.0,
    ):
        """Stream live CARLA signals to AUTOFORGE service endpoint."""
        print(f"[CARLA] Streaming signals to services at {service_url}")
        client = ServiceClient(service_url, transport=transport)
        logger = CarlaValidationLogger(Path(log_path))

        period = 1.0 / rate_hz if rate_hz > 0 else 0.1
        samples = 0

        try:
            while True:
                signals = self.get_vehicle_signals()

                start = time.time()
                response = client.send_bms_signals(signals)
                latency_ms = (time.time() - start) * 1000.0

                if response:
                    self._log_predictions(signals, response)
                    logger.log(signals, response, latency_ms)
                    samples += 1

                if max_samples and samples >= max_samples:
                    print(f"[CARLA] Reached max_samples={max_samples}, stopping stream.")
                    break

                time.sleep(period)

        except KeyboardInterrupt:
            print("\n[CARLA] Bridge stopped by user")
        finally:
            logger.save()
            print(f"[CARLA] Validation log saved: {log_path}")

    def _log_predictions(self, signals: Dict[str, Any], response: Dict[str, Any]):
        """Print warning summary from service response."""
        timestamp = self.world.get_snapshot().timestamp.elapsed_seconds

        warnings = response.get('warnings', [])
        if warnings:
            print(f"\n[WARN] [{timestamp:.1f}s] WARNINGS:")
            for warning in warnings:
                code = warning.get('code', 0)
                message = warning.get('message', '')
                print(f"    {code:04X}: {message}")

    def cleanup(self):
        """Clean up CARLA actors."""
        if self.vehicle:
            print("[CARLA] Destroying vehicle...")
            self.vehicle.destroy()


def _iter_replay_signals(replay_input: Path) -> Iterable[Dict[str, Any]]:
    """
    Load replay signals from JSON.

    Supported formats:
    - {"records": [{"signals": {...}}, ...]}
    - [{"signals": {...}}, ...]
    - [{...signal fields...}, ...]
    """
    if not replay_input.exists():
        raise FileNotFoundError(f"Replay input not found: {replay_input}")

    data = json.loads(replay_input.read_text())
    records: List[Any]
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        records = data["records"]
    elif isinstance(data, list):
        records = data
    else:
        raise ValueError("Replay JSON must be a list or an object with a 'records' list")

    for idx, item in enumerate(records, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Replay record at index {idx} is not an object")
        if isinstance(item.get("signals"), dict):
            yield item["signals"]
        else:
            yield item


def replay_to_services(
    replay_input: Path,
    service_url: str,
    log_path: str,
    transport: str = "rest",
    max_samples: int = 0,
    rate_hz: float = 10.0,
) -> None:
    """Replay recorded signals through the standard service+logger path."""
    print(f"[REPLAY] Loading replay from {replay_input}")
    client = ServiceClient(service_url, transport=transport)
    logger = CarlaValidationLogger(Path(log_path))
    period = 1.0 / rate_hz if rate_hz > 0 else 0.1

    count = 0
    for signals in _iter_replay_signals(replay_input):
        start = time.time()
        response = client.send_bms_signals(signals)
        latency_ms = (time.time() - start) * 1000.0
        logger.log(signals, response, latency_ms)
        count += 1

        if max_samples and count >= max_samples:
            break
        time.sleep(period)

    logger.save()
    print(f"[REPLAY] Processed {count} samples")
    print(f"[REPLAY] Validation log saved: {log_path}")


def main():
    """Main entry point for CARLA bridge."""
    parser = argparse.ArgumentParser(description='AUTOFORGE CARLA Integration Bridge')
    parser.add_argument('--mode', choices=['live', 'replay'], default='replay',
                        help='Run in live CARLA mode or replay mode')
    parser.add_argument('--host', default='localhost', help='CARLA host')
    parser.add_argument('--port', type=int, default=2000, help='CARLA port')
    parser.add_argument('--service-url', default='http://localhost:30509',
                        help='AUTOFORGE service URL')
    parser.add_argument(
        '--transport',
        choices=['rest', 'someip'],
        default='rest',
        help='Protocol abstraction transport for service call',
    )
    parser.add_argument('--log-path', default='output/carla_validation.json',
                        help='Path to CARLA validation log JSON')
    parser.add_argument('--replay-input', default='',
                        help='Replay JSON file path (required for replay mode)')
    parser.add_argument('--max-samples', type=int, default=0,
                        help='Stop after N samples (0 means unlimited)')
    parser.add_argument('--rate-hz', type=float, default=10.0,
                        help='Sample/replay rate in Hz')

    args = parser.parse_args()

    try:
        if args.mode == 'replay':
            if not args.replay_input:
                raise ValueError('--replay-input is required when --mode replay')

            print("\n" + "=" * 60)
            print("AUTOFORGE CARLA BRIDGE - REPLAY MODE")
            print("=" * 60)

            replay_to_services(
                replay_input=Path(args.replay_input),
                service_url=args.service_url,
                log_path=args.log_path,
                transport=args.transport,
                max_samples=args.max_samples,
                rate_hz=args.rate_hz,
            )
            return

        bridge = CARLABridge(args.host, args.port)
        bridge.spawn_test_vehicle()

        print("\n" + "=" * 60)
        print("AUTOFORGE CARLA BRIDGE - LIVE MODE")
        print("=" * 60)
        print("Vehicle signals streaming to services...")
        print("Press Ctrl+C to stop\n")

        bridge.stream_to_services(
            service_url=args.service_url,
            log_path=args.log_path,
            transport=args.transport,
            max_samples=args.max_samples,
            rate_hz=args.rate_hz,
        )

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'bridge' in locals():
            bridge.cleanup()


if __name__ == '__main__':
    main()
