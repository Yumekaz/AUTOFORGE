#include <iostream>
#include <string>
#include <cmath>

class TirePressureDiagnosticService {
public:
    struct TireStatus {
        float tire_pressure_fl;
        float tire_pressure_fr;
        float tire_pressure_rl;
        float tire_pressure_rr;
        float failure_risk;
    };

    struct WarningEvent {
        uint16_t warning_code;
        std::string warning_message;
    };

    TirePressureDiagnosticService() : tire_pressure_fl(0.0), tire_pressure_fr(0.0), tire_pressure_rl(0.0), tire_pressure_rr(0.0) {}

    void setTirePressures(float fl, float fr, float rl, float rr) {
        tire_pressure_fl = fl;
        tire_pressure_fr = fr;
        tire_pressure_rl = rl;
        tire_pressure_rr = rr;
    }

    TireStatus GetTireStatus() const {
        TireStatus status;
        status.tire_pressure_fl = tire_pressure_fl;
        status.tire_pressure_fr = tire_pressure_fr;
        status.tire_pressure_rl = tire_pressure_rl;
        status.tire_pressure_rr = tire_pressure_rr;
        status.failure_risk = calculateFailureRisk();
        return status;
    }

    WarningEvent emitTireWarning() const {
        if (tire_pressure_fl < 2.0 || tire_pressure_fr < 2.0 || tire_pressure_rl < 2.0 || tire_pressure_rr < 2.0) {
            return {0x0101, "Low tire pressure"};
        } else if (std::abs(tire_pressure_fl - tire_pressure_fr) > 0.4 || std::abs(tire_pressure_rl - tire_pressure_rr) > 0.4) {
            return {0x0102, "Tire pressure imbalance"};
        }
        return {};
    }

private:
    float calculateFailureRisk() const {
        // Placeholder for failure risk calculation
        return 0.0;
    }

    float tire_pressure_fl;
    float tire_pressure_fr;
    float tire_pressure_rl;
    float tire_pressure_rr;
};

int main() {
    TirePressureDiagnosticService service;
    service.setTirePressures(3.0, 3.5, 2.8, 2.9);
    auto status = service.GetTireStatus();
    std::cout << "Tire Pressure FL: " << status.tire_pressure_fl << std::endl;
    std::cout << "Tire Pressure FR: " << status.tire_pressure_fr << std::endl;
    std::cout << "Tire Pressure RL: " << status.tire_pressure_rl << std::endl;
    std::cout << "Tire Pressure RR: " << status.tire_pressure_rr << std::endl;

    auto warning = service.emitTireWarning();
    if (warning.warning_code != 0) {
        std::cout << "Warning Code: " << warning.warning_code << ", Message: " << warning.warning_message << std::endl;
    }

    return 0;
}