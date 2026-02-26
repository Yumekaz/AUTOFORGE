#include "vsomeip_service.hpp"
#include <iostream>

BMSDiagnosticServiceJavaService::BMSDiagnosticServiceJavaService() = default;

bool BMSDiagnosticServiceJavaService::init() {
    app_ = vsomeip::runtime::get()->create_application("BMSDiagnosticServiceJava_app");
    if (!app_ || !app_->init()) return false;

    app_->register_message_handler(0x1001, 0x1, 0x1, std::bind(&BMSDiagnosticServiceJavaService::on_getbatterystatus, this, std::placeholders::_1));
    app_->register_message_handler(0x1001, 0x1, 0x2, std::bind(&BMSDiagnosticServiceJavaService::on_getcellvoltages, this, std::placeholders::_1));
    app_->register_message_handler(0x1001, 0x1, 0x3, std::bind(&BMSDiagnosticServiceJavaService::on_getestimatedrange, this, std::placeholders::_1));
    app_->offer_service(SERVICE_ID, INSTANCE_ID);
    return true;
}

void BMSDiagnosticServiceJavaService::start() {
    app_->start();
}

void BMSDiagnosticServiceJavaService::stop() {
    if (app_) app_->stop();
}

void BMSDiagnosticServiceJavaService::on_getbatterystatus(const std::shared_ptr<vsomeip::message>& request) {
    // Protocol Abstraction skeleton:
    // Map request payload to domain DTO, call existing service logic, return response.
    auto response = vsomeip::runtime::get()->create_response(request);
    // TODO: serialize BMS diagnostics response payload here.
    app_->send(response);
}

void BMSDiagnosticServiceJavaService::on_getcellvoltages(const std::shared_ptr<vsomeip::message>& request) {
    // Protocol Abstraction skeleton:
    // Map request payload to domain DTO, call existing service logic, return response.
    auto response = vsomeip::runtime::get()->create_response(request);
    // TODO: serialize BMS diagnostics response payload here.
    app_->send(response);
}

void BMSDiagnosticServiceJavaService::on_getestimatedrange(const std::shared_ptr<vsomeip::message>& request) {
    // Protocol Abstraction skeleton:
    // Map request payload to domain DTO, call existing service logic, return response.
    auto response = vsomeip::runtime::get()->create_response(request);
    // TODO: serialize BMS diagnostics response payload here.
    app_->send(response);
}
