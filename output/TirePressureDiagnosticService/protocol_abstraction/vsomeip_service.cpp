#include "vsomeip_service.hpp"
#include <iostream>

TirePressureDiagnosticServiceService::TirePressureDiagnosticServiceService() = default;

bool TirePressureDiagnosticServiceService::init() {
    app_ = vsomeip::runtime::get()->create_application("TirePressureDiagnosticService_app");
    if (!app_ || !app_->init()) return false;

    app_->register_message_handler(0x1101, 0x1, 0x1, std::bind(&TirePressureDiagnosticServiceService::on_gettirestatus, this, std::placeholders::_1));
    app_->offer_service(SERVICE_ID, INSTANCE_ID);
    return true;
}

void TirePressureDiagnosticServiceService::start() {
    app_->start();
}

void TirePressureDiagnosticServiceService::stop() {
    if (app_) app_->stop();
}

void TirePressureDiagnosticServiceService::on_gettirestatus(const std::shared_ptr<vsomeip::message>& request) {
    // Protocol Abstraction skeleton:
    // Map request payload to domain DTO, call existing service logic, return response.
    auto response = vsomeip::runtime::get()->create_response(request);
    // TODO: serialize BMS diagnostics response payload here.
    app_->send(response);
}
