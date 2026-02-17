#include <someip/someip.hpp>
#include <iostream>
#include <string>
#include <vector>

#define SOMEIP_SERVICE_ID 0x1234
#define SOMEIP_INSTANCE_ID 0x0001
#define SOMEIP_METHOD_ID_GET_MOTOR_HEALTH 0x0001
#define SOMEIP_EVENT_ID_MOTOR_WARNING 0x8001

class MotorHealthDiagnosticService {
public:
    MotorHealthDiagnosticService(someip::client_t client_id) : client_(client_id), someip_client_(nullptr) {}

    void init(someip::runtime* runtime, const std::string& service_name) {
        someip_client_ = runtime->create_client(client_);
        if (someip_client_) {
            someip_client_->init();
            someip_client_->register_event(SOMEIP_SERVICE_ID, SOMEIP_INSTANCE_ID, SOMEIP_EVENT_ID_MOTOR_WARNING);
            someip_client_->subscribe(SOMEIP_SERVICE_ID, SOMEIP_INSTANCE_ID, SOMEIP_EVENT_ID_MOTOR_WARNING, std::bind(&MotorHealthDiagnosticService::on_motor_warning_event, this, std::placeholders::_1));
        }
    }

    void start() {
        if (someip_client_) {
            someip_client_->start();
        }
    }

    void stop() {
        if (someip_client_) {
            someip_client_->stop();
        }
    }

    void handle_motor_temperature(float temperature) {
        if (temperature > 85.0f) {
            emit_event(0x0201, "Motor temperature high");
        } else if (temperature > 100.0f) {
            emit_event(0x0202, "Motor critical temperature");
        }
    }

private:
    someip::client_t client_;
    someip::client* someip_client_;

    void on_motor_warning_event(const someip::message& request) {
        // Handle incoming event
    }

    void emit_event(uint16_t warning_code, const std::string& warning_message) {
        if (someip_client_) {
            someip::message_ptr response = someip::runtime::get()->create_response(request);
            response->set_payload(warning_code, warning_message);
            someip_client_->send(response);
        }
    }
};

int main() {
    someip::runtime* runtime = someip::runtime::get();
    MotorHealthDiagnosticService service(123456789);

    service.init(runtime, "MotorHealthDiagnosticService");
    service.start();

    // Simulate motor temperature readings
    service.handle_motor_temperature(90.0f);
    service.handle_motor_temperature(105.0f);
    service.handle_motor_temperature(75.0f);

    service.stop();
    return 0;
}