#!/usr/bin/env python3
"""
AUTOFORGE CARLA Integration Bridge
Connects CARLA simulation to generated AUTOFORGE services for real-time testing.

This script:
1. Connects to CARLA simulator
2. Spawns a test vehicle
3. Streams vehicle signals to generated services
4. Receives health predictions and alerts
5. Logs results for validation
"""

import carla
import time
import json
from typing import Dict, Any
import sys
import os
from pathlib import Path

# Add AUTOFORGE src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
sys.path.insert(0, os.path.dirname(__file__))

from service_client import ServiceClient
from carla_validation_logger import CarlaValidationLogger


class CARLABridge:
    """Bridge between CARLA simulation and AUTOFORGE services."""
    
    def __init__(self, carla_host: str = 'localhost', carla_port: int = 2000):
        self.client = carla.Client(carla_host, carla_port)
        self.client.set_timeout(10.0)
        self.world = self.client.get_world()
        self.vehicle = None
        self.sensors = {}
        
    def spawn_test_vehicle(self):
        """Spawn a test vehicle with all required sensors."""
        print("[CARLA] Spawning test vehicle...")
        
        # Get vehicle blueprint
        blueprint_library = self.world.get_blueprint_library()
        vehicle_bp = blueprint_library.filter('vehicle.tesla.model3')[0]
        
        # Spawn at a random spawn point
        spawn_points = self.world.get_map().get_spawn_points()
        spawn_point = spawn_points[0] if spawn_points else carla.Transform()
        
        self.vehicle = self.world.spawn_actor(vehicle_bp, spawn_point)
        print(f"[CARLA] Vehicle spawned: {self.vehicle.type_id}")
        
        # Attach sensors
        self._attach_sensors()
        
    def _attach_sensors(self):
        """Attach all vehicle sensors required by AUTOFORGE services."""
        # This would attach actual CARLA sensors
        # For now, we'll use the vehicle's built-in telemetry
        pass
        
    def get_vehicle_signals(self) -> Dict[str, Any]:
        """
        Extract all vehicle signals required by AUTOFORGE services.
        
        Returns comprehensive signal set matching vehicle_signals.yaml
        """
        if not self.vehicle:
            return {}
        
        # Get vehicle physics
        physics = self.vehicle.get_physics_control()
        transform = self.vehicle.get_transform()
        velocity = self.vehicle.get_velocity()
        control = self.vehicle.get_control()
        
        # Calculate derived values
        speed_mps = (velocity.x**2 + velocity.y**2 + velocity.z**2)**0.5
        speed_kmh = speed_mps * 3.6
        
        # Extract all signals (matching one-pager Artifact D)
        signals = {
            # Driving dynamics
            'vehicle_speed': speed_kmh,
            'gear_position': control.gear,
            'throttle_position': control.throttle * 100.0,
            'brake_pressure': control.brake * 200.0,  # Scaled to bar
            'steering_angle': control.steer * 540.0,  # Scaled to degrees
            
            # Battery/EV (simulated - CARLA doesn't provide these)
            'battery_soc': self._simulate_battery_soc(),
            'battery_voltage': 400.0,  # Nominal EV voltage
            'battery_current': control.throttle * 200.0 - control.brake * 100.0,
            'battery_temperature': self._simulate_battery_temp(),
            'estimated_range': self._estimate_range(),
            
            # Tire pressure (simulated)
            'tire_pressure_fl': 2.5,  # bar (nominal)
            'tire_pressure_fr': 2.5,
            'tire_pressure_rl': 2.4,
            'tire_pressure_rr': 2.4,
            
            # Motor (simulated)
            'motor_temperature': 50.0 + control.throttle * 30.0,
            'motor_torque': control.throttle * 350.0,
            'motor_power': (control.throttle * 350.0 * speed_mps) / 1000.0,  # kW
            
            # Environment
            'ambient_temperature': 25.0,
            'odometer': 12345.0,
        }
        
        return signals
    
    def _simulate_battery_soc(self) -> float:
        """Simulate battery state of charge degradation."""
        # In real integration, this would come from actual battery model
        elapsed_time = self.world.get_snapshot().timestamp.elapsed_seconds
        return max(20.0, 100.0 - (elapsed_time / 100.0))  # Degrades over time
    
    def _simulate_battery_temp(self) -> float:
        """Simulate battery temperature based on usage."""
        if not self.vehicle:
            return 25.0
        control = self.vehicle.get_control()
        # Temperature rises with throttle
        return 25.0 + control.throttle * 20.0
    
    def _estimate_range(self) -> float:
        """Estimate remaining range based on SOC."""
        soc = self._simulate_battery_soc()
        return soc * 4.0  # 400km at 100% SOC
    
    def stream_to_services(self, service_url: str = 'http://bms-service:30509', log_path: str = 'output/carla_validation.json'):
        """
        Stream vehicle signals to AUTOFORGE-generated services.
        This demonstrates the full integration loop.
        """
        print(f"[CARLA] Streaming signals to services at {service_url}")
        client = ServiceClient(service_url)
        logger = CarlaValidationLogger(Path(log_path))
        
        try:
            while True:
                # Get current vehicle state
                signals = self.get_vehicle_signals()
                
                # Send to BMS service
                start = time.time()
                response = client.send_bms_signals(signals)
                latency_ms = (time.time() - start) * 1000.0
                
                # Log predictions
                if response:
                    self._log_predictions(signals, response)
                    logger.log(signals, response, latency_ms)
                
                time.sleep(0.1)  # 10Hz update rate
                
        except KeyboardInterrupt:
            print("\n[CARLA] Bridge stopped by user")
        finally:
            logger.save()
    
    def _send_to_bms_service(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Deprecated: simulated service response."""
        return {}
    
    def _log_predictions(self, signals: Dict[str, Any], response: Dict[str, Any]):
        """Log vehicle state and service predictions."""
        timestamp = self.world.get_snapshot().timestamp.elapsed_seconds
        
        log_entry = {
            'timestamp': timestamp,
            'vehicle_state': {
                'speed': signals['vehicle_speed'],
                'battery_soc': signals['battery_soc'],
                'battery_temp': signals['battery_temperature'],
            },
            'service_response': response
        }
        
        # Print warnings if any
        if response['warnings']:
            print(f"\n⚠️  [{timestamp:.1f}s] WARNINGS:")
            for warning in response['warnings']:
                print(f"    {warning['code']:04X}: {warning['message']}")
    
    def cleanup(self):
        """Clean up CARLA actors."""
        if self.vehicle:
            print("[CARLA] Destroying vehicle...")
            self.vehicle.destroy()


def main():
    """Main entry point for CARLA bridge."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AUTOFORGE CARLA Integration Bridge')
    parser.add_argument('--host', default='localhost', help='CARLA host')
    parser.add_argument('--port', type=int, default=2000, help='CARLA port')
    parser.add_argument('--service-url', default='http://bms-service:30509',
                       help='AUTOFORGE service URL')
    parser.add_argument('--log-path', default='output/carla_validation.json',
                       help='Path to CARLA validation log JSON')
    
    args = parser.parse_args()
    
    try:
        # Create bridge
        bridge = CARLABridge(args.host, args.port)
        
        # Spawn vehicle
        bridge.spawn_test_vehicle()
        
        # Start streaming
        print("\n" + "="*60)
        print("AUTOFORGE CARLA BRIDGE - RUNNING")
        print("="*60)
        print("Vehicle signals streaming to services...")
        print("Press Ctrl+C to stop\n")
        
        bridge.stream_to_services(args.service_url, args.log_path)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'bridge' in locals():
            bridge.cleanup()


if __name__ == '__main__':
    main()
