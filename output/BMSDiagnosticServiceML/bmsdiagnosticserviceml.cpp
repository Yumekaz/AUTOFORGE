#include <someip/someip.hpp>
#include <iostream>
#include <string>
#include <stdexcept>
#include "tire_failure_bar.onnx_inference.h"

class BMSDiagnosticServiceML {
public:
    void init() {
        // Initialize SOME/IP service
        someip_service_ = std::make_shared<someip::service>(4097, 1);
        someip_service_->register_event(32769);
        someip_service_->register_method(1);
        someip_service_->register_method(3);

        // Register event handler
        someip_service_->set_event_handler([this](const std::shared_ptr<someip::message> &request) {
            handleBatteryWarning(request);
        });

        // Register method handlers
        someip_service_->set_request_handler([this](const std::shared_ptr<someip::message> &request) {
            if (request->get_method() == 1) {
                return handleGetBatteryStatus(request);
            } else if (request->get_method() == 3) {
                return handleGetEstimatedRange(request);
            }
        });
    }

    void start() {
        someip_service_->start();
    }

private:
    std::shared_ptr<someip::service> someip_service_;

    std::shared_ptr<someip::message> handleBatteryWarning(const std::shared_ptr<someip::message> &request) {
        uint16_t warning_code = 0;
        std::string warning_message;

        // Check battery SOC
        if (battery_soc_ < 20) {
            warning_code = 0x0001;
            warning_message = "Low battery";
        } else if (battery_temperature_ > 45) {
            warning_code = 0x0002;
            warning_message = "High temperature";
        } else if (battery_temperature_ > 60) {
            warning_code = 0x0003;
            warning_message = "Critical temperature - shutdown required";
        }

        if (warning_code != 0) {
            someip::event event(32769, 1);
            event.set_field("code", warning_code);
            event.set_field("msg", warning_message);
            someip_service_->send_event(event);
        }

        return nullptr;
    }

    std::shared_ptr<someip::message> handleGetBatteryStatus(const std::shared_ptr<someip::message> &request) {
        someip::response response(request->get_request_id(), request->get_instance());
        response.set_field("soc", battery_soc_);
        response.set_field("voltage", battery_voltage_);
        response.set_field("current", battery_current_);
        response.set_field("temperature", battery_temperature_);
        response.set_field("health_status", battery_health_status_);

        return response;
    }

    std::shared_ptr<someip::message> handleGetEstimatedRange(const std::shared_ptr<someip::message> &request) {
        uint8_t driving_mode = request->get_payload()[0];
        float range_km;

        // Calculate estimated range based on driving mode
        if (driving_mode == 1) {
            range_km = 200.0;
        } else {
            range_km = 150.0; // Default value for other modes
        }

        someip::response response(request->get_request_id(), request->get_instance());
        response.set_field("range_km", range_km);

        return response;
    }
};

int main() {
    BMSDiagnosticServiceML service;
    service.init();
    service.start();

    return 0;
}