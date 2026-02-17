#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <someip/someip.hpp>

class BMSDiagnosticService {
public:
    void init(std::shared_ptr<someip::client> client) {
        client_ = client;
        client_->register_message_handler(4097, 1, std::bind(&BMSDiagnosticService::handle_get_battery_status, this, std::placeholders::_1));
        client_->register_message_handler(4097, 2, std::bind(&BMSDiagnosticService::handle_get_cell_voltages, this, std::placeholders::_1));
        client_->register_message_handler(4097, 3, std::bind(&BMSDiagnosticService::handle_get_estimated_range, this, std::placeholders::_1));
    }

    void handle_get_battery_status(const someip::message& request) {
        auto response = someip::message::create(request.get_service(), request.getMethod(), request.getInstance(), request.getClient());
        response->set_payload(create_bms_status_payload());

        client_->send(response);
    }

    void handle_get_cell_voltages(const someip::message& request) {
        auto response = someip::message::create(request.get_service(), request.getMethod(), request.getInstance(), request.getClient());
        response->set_payload(create_cell_voltages_payload());

        client_->send(response);
    }

    void handle_get_estimated_range(const someip::message& request) {
        uint8_t driving_mode = 1;
        if (request.get_payload().size() >= sizeof(driving_mode)) {
            std::memcpy(&driving_mode, request.get_payload().data(), sizeof(driving_mode));
        }

        auto response = someip::message::create(request.get_service(), request.getMethod(), request.getInstance(), request.getClient());
        response->set_payload(create_estimated_range_payload(driving_mode));

        client_->send(response);
    }

private:
    std::shared_ptr<someip::client> client_;

    std::vector<uint8_t> create_bms_status_payload() {
        BMSStatus status = get_battery_status();
        std::vector<uint8_t> payload;
        payload.push_back(static_cast<uint8_t>(status.soc * 100));
        payload.push_back(static_cast<uint8_t>(status.voltage * 100));
        payload.push_back(static_cast<uint8_t>(status.current * 100));
        payload.push_back(static_cast<uint8_t>(status.temperature * 100));
        payload.push_back(status.health_status);
        return payload;
    }

    std::vector<uint8_t> create_cell_voltages_payload() {
        CellVoltages voltages = get_cell_voltages();
        std::vector<uint8_t> payload;
        for (float voltage : voltages.cell_voltages) {
            payload.push_back(static_cast<uint8_t>(voltage * 100));
        }
        return payload;
    }

    std::vector<uint8_t> create_estimated_range_payload(uint8_t driving_mode) {
        EstimatedRange range = get_estimated_range(driving_mode);
        std::vector<uint8_t> payload;
        payload.push_back(static_cast<uint8_t>(range.range_km * 100));
        return payload;
    }

    BMSStatus get_battery_status() {
        BMSStatus status;
        status.soc = 50.0;
        status.voltage = 420.0;
        status.current = 10.0;
        status.temperature = 30.0;

        if (status.soc < 20) {
            emit_warning(0x0001, "Low battery");
        }
        if (status.temperature > 45) {
            emit_warning(0x0002, "High temperature");
        }
        if (status.temperature > 60) {
            emit_warning(0x0003, "Critical temperature - shutdown required");
        }

        return status;
    }

    CellVoltages get_cell_voltages() {
        CellVoltages voltages;
        voltages.cell_voltages = {3.7, 3.8, 3.9};
        return voltages;
    }

    EstimatedRange get_estimated_range(uint8_t driving_mode) {
        EstimatedRange range;
        if (driving_mode == 0) {
            range.range_km = 200.0;
        } else if (driving_mode == 1) {
            range.range_km = 400.0;
        } else if (driving_mode == 2) {
            range.range_km = 600.0;
        }
        return range;
    }

    void emit_warning(uint16_t code, const std::string& message) {
        // Implement warning emission logic here
    }
};

struct BMSStatus {
    float soc;
    float voltage;
    float current;
    float temperature;
    uint8_t health_status;
};

struct CellVoltages {
    std::vector<float> cell_voltages;
};

struct EstimatedRange {
    float range_km;
};