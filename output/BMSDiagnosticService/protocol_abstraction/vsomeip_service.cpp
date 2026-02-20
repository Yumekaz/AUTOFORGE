#include "vsomeip_service.hpp"
#include <iostream>

BMSDiagnosticServiceService::BMSDiagnosticServiceService() = default;

bool BMSDiagnosticServiceService::init() {
    app_ = vsomeip::runtime::get()->create_application("BMSDiagnosticService_app");
    if (!app_ || !app_->init()) return false;

    app_->register_message_handler(0x1001, 0x1, 0x1, std::bind(&BMSDiagnosticServiceService::on_getbatterystatus, this, std::placeholders::_1));
    app_->register_message_handler(0x1001, 0x1, 0x2, std::bind(&BMSDiagnosticServiceService::on_getcellvoltages, this, std::placeholders::_1));
    app_->register_message_handler(0x1001, 0x1, 0x3, std::bind(&BMSDiagnosticServiceService::on_getestimatedrange, this, std::placeholders::_1));
    app_->offer_service(SERVICE_ID, INSTANCE_ID);
    return true;
}

void BMSDiagnosticServiceService::start() {
    app_->start();
}

void BMSDiagnosticServiceService::stop() {
    if (app_) app_->stop();
}

void BMSDiagnosticServiceService::on_getbatterystatus(const std::shared_ptr<vsomeip::message>& request) {
    // Protocol Abstraction skeleton:
    // Map request payload to domain DTO, call existing service logic, return response.
    auto response = vsomeip::runtime::get()->create_response(request);
    // TODO: serialize BMS diagnostics response payload here.
    app_->send(response);
}

void BMSDiagnosticServiceService::on_getcellvoltages(const std::shared_ptr<vsomeip::message>& request) {
    // Protocol Abstraction skeleton:
    // Map request payload to domain DTO, call existing service logic, return response.
    auto response = vsomeip::runtime::get()->create_response(request);
    // TODO: serialize BMS diagnostics response payload here.
    app_->send(response);
}

void BMSDiagnosticServiceService::on_getestimatedrange(const std::shared_ptr<vsomeip::message>& request) {
    // Protocol Abstraction skeleton:
    // Map request payload to domain DTO, call existing service logic, return response.
    auto response = vsomeip::runtime::get()->create_response(request);
    // TODO: serialize BMS diagnostics response payload here.
    app_->send(response);
}
