#include <someip_client.hpp>
#include <iostream>
#include <string>
#include <array>

class BMSDiagnosticService {
public:
    void Initialize() {
        // Lifecycle initialization
    }

    void Shutdown() {
        // Lifecycle shutdown
    }

    std::map<uint32_t, float> GetBatteryStatus() const {
        return battery_status_;
    }

    std::vector<float> GetCellVoltages() const {
        return cell_voltages_;
    }

    float GetEstimatedRange(uint8_t driving_mode) const {
        switch (driving_mode) {
            case 0:
                return 200.0;
            case 1:
                return 300.0;
            case 2:
                return 400.0;
            default:
                throw std::invalid_argument("Invalid driving mode");
        }
    }

private:
    std::map<uint32_t, float> battery_status_ = {
        {1, 50.0}, {2, 420.0}, {3, 10.0}, {4, 30.0}, {5, 0}
    };
    std::vector<float> cell_voltages_ = {3.7, 3.8, 3.9};
};

int main() {
    BMSDiagnosticService service;
    service.Initialize();

    // Test cases
    assert(service.GetBatteryStatus()[1] == 50.0);
    assert(service.GetCellVoltages()[0] == 3.7);
    assert(service.GetEstimatedRange(0) == 200.0);

    service.Shutdown();
    return 0;
}