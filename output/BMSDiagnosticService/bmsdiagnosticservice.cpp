
#include "bms_diagnostic_service.hpp"
#include <vsomeip/vsomeip.hpp>

class BMSDiagnosticService {
public:
    struct BatteryStatus {
        float soc;
        float voltage;
        float current;
        float temperature;
        uint8_t health_status;
    };
    
    BatteryStatus GetBatteryStatus() {
        BatteryStatus status;
        status.soc = battery_soc_;
        status.voltage = battery_voltage_;
        status.current = battery_current_;
        status.temperature = battery_temperature_;
        status.health_status = CalculateHealthStatus();
        return status;
    }
    
private:
    uint8_t CalculateHealthStatus() {
        if (battery_temperature_ > 60) return 2;  // CRITICAL
        if (battery_temperature_ > 45 || battery_soc_ < 20) return 1;  // WARNING
        return 0;  // OK
    }
    
    float battery_soc_ = 0.0f;
    float battery_voltage_ = 0.0f;
    float battery_current_ = 0.0f;
    float battery_temperature_ = 0.0f;
};
