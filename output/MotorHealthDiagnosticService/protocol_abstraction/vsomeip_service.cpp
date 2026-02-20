#include "vsomeip_service.hpp"
#include <iostream>

MotorHealthDiagnosticServiceService::MotorHealthDiagnosticServiceService() = default;

bool MotorHealthDiagnosticServiceService::init() {
    app_ = vsomeip::runtime::get()->create_application("MotorHealthDiagnosticService_app");
    if (!app_ || !app_->init()) return false;

    app_->register_message_handler(0x1201, 0x1, 0x1, std::bind(&MotorHealthDiagnosticServiceService::on_getmotorhealth, this, std::placeholders::_1));
    app_->offer_service(SERVICE_ID, INSTANCE_ID);
    return true;
}

void MotorHealthDiagnosticServiceService::start() {
    app_->start();
}

void MotorHealthDiagnosticServiceService::stop() {
    if (app_) app_->stop();
}

void MotorHealthDiagnosticServiceService::on_getmotorhealth(const std::shared_ptr<vsomeip::message>& request) {
    // Protocol Abstraction skeleton:
    // Map request payload to domain DTO, call existing service logic, return response.
    auto response = vsomeip::runtime::get()->create_response(request);
    // TODO: serialize BMS diagnostics response payload here.
    app_->send(response);
}
