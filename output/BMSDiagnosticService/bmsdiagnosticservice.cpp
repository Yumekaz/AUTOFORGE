#include <iostream>
#include <string>
#include <vector>
#include <cstdint>
#include <memory>

// Mock SOME/IP client for testing
class MockSOMEIPClient {
public:
    struct BatteryStatusResponse {
        float soc;
        float voltage;
        float current;
        float temperature;
        uint8_t health_status;
    };

    struct CellVoltagesResponse {
        std::vector<float> cell_voltages;
    };

    struct EstimatedRangeResponse {
        float range_km;
    };

    BatteryStatusResponse GetBatteryStatus() const {
        return {50.0, 420.0, 10.0, 30.0, 0};
    }

    CellVoltagesResponse GetCellVoltages() const {
        return {{3.7f} * 8};
    }

    EstimatedRangeResponse GetEstimatedRange(uint8_t driving_mode) const {
        switch (driving_mode) {
            case 0: return {200.0f};
            case 1: return {300.0f};
            case 2: return {400.0f};
            default: return {0.0f};
        }
    }
};

class BMSDiagnosticService {
public:
    BMSDiagnosticService() : client_(std::make_shared<MockSOMEIPClient>()) {}

    struct BatteryStatusResponse {
        float soc;
        float voltage;
        float current;
        float temperature;
        uint8_t health_status;
    };

    struct CellVoltagesResponse {
        std::vector<float> cell_voltages;
    };

    struct EstimatedRangeResponse {
        float range_km;
    };

    BatteryStatusResponse GetBatteryStatus() const {
        auto response = client_->GetBatteryStatus();
        if (response.temperature > 60.0f) {
            emitWarning(0x0003, "Critical temperature - shutdown required");
        } else if (response.temperature > 45.0f) {
            emitWarning(0x0002, "High temperature");
        } else if (response.soc < 20.0f) {
            emitWarning(0x0001, "Low battery");
        }
        return response;
    }

    CellVoltagesResponse GetCellVoltages() const {
        return client_->GetCellVoltages();
    }

    EstimatedRangeResponse GetEstimatedRange(uint8_t driving_mode = 1) const {
        return client_->GetEstimatedRange(driving_mode);
    }

private:
    void emitWarning(uint16_t code, const std::string& message) const {
        // Emit warning event here
        std::cout << "Battery Warning: Code=" << code << ", Message=" << message << std::endl;
    }

    std::shared_ptr<MockSOMEIPClient> client_;
};

int main() {
    BMSDiagnosticService bms_service;

    auto battery_status = bms_service.GetBatteryStatus();
    assert(battery_status.soc == 50.0f);
    assert(battery_status.voltage == 420.0f);
    assert(battery_status.current == 10.0f);
    assert(battery_status.temperature == 30.0f);
    assert(battery_status.health_status == 0);

    auto cell_voltages = bms_service.GetCellVoltages();
    assert(cell_voltages.cell_voltages.size() == 8);
    for (const auto& voltage : cell_voltages.cell_voltages) {
        assert(voltage == 3.7f);
    }

    auto estimated_range_eco = bms_service.GetEstimatedRange(0);
    assert(estimated_range_eco.range_km == 200.0f);

    auto estimated_range_normal = bms_service.GetEstimatedRange(1);
    assert(estimated_range_normal.range_km == 300.0f);

    auto estimated_range_sport = bms_service.GetEstimatedRange(2);
    assert(estimated_range_sport.range_km == 400.0f);

    return 0;
}