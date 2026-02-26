#pragma once
#include <cstdint>
#include <memory>
#include <vsomeip/vsomeip.hpp>

class BMSDiagnosticServiceJavaService {
public:
    BMSDiagnosticServiceJavaService();
    bool init();
    void start();
    void stop();

    static constexpr uint16_t SERVICE_ID = 0x1001;
    static constexpr uint16_t INSTANCE_ID = 0x1;
    static constexpr uint16_t GETBATTERYSTATUS_ID = 0x1;
static constexpr uint16_t GETCELLVOLTAGES_ID = 0x2;
static constexpr uint16_t GETESTIMATEDRANGE_ID = 0x3;
    static constexpr uint16_t BATTERYWARNING_ID = 0x8001;

private:
    std::shared_ptr<vsomeip::application> app_;
        void on_getbatterystatus(const std::shared_ptr<vsomeip::message>& request);
    void on_getcellvoltages(const std::shared_ptr<vsomeip::message>& request);
    void on_getestimatedrange(const std::shared_ptr<vsomeip::message>& request);
};
