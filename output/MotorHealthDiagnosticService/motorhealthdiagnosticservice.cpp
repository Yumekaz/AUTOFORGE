#include <cstdint>
#include <string>
#include <stdexcept>
#include <memory>

class MotorHealthDiagnosticService {
public:
    struct HealthStatus {
        float motor_temperature;
        float motor_torque;
        float motor_power;
        uint8_t health_status;
    };

    struct WarningEvent {
        uint16_t warning_code;
        std::string warning_message;
    };

    void emit_MotorWarning(uint16_t code, const std::string& msg) {
        // Implement event emission logic here
        // For example:
        // MotorWarningEvent event{code, msg};
        // someip_service->emit_event(event);
    }

    HealthStatus GetMotorHealth(float motor_temperature = 0.0f,
                                 float motor_torque = 0.0f,
                                 float motor_power = 0.0f) {
        if (motor_temperature < -50.0f || motor_temperature > 150.0f) {
            throw std::invalid_argument("Invalid motor temperature");
        }
        if (motor_torque < 0.0f) {
            throw std::invalid_argument("Invalid motor torque");
        }
        if (motor_power < 0.0f) {
            throw std::invalid_argument("Invalid motor power");
        }

        HealthStatus status;
        status.motor_temperature = motor_temperature;
        status.motor_torque = motor_torque;
        status.motor_power = motor_power;

        if (motor_temperature > 85.0f) {
            emit_MotorWarning(0x0201, "Motor temperature high");
        }
        if (motor_temperature > 100.0f) {
            emit_MotorWarning(0x0202, "Motor critical temperature");
        }

        status.health_status = 0; // Normal health status
        return status;
    }
};