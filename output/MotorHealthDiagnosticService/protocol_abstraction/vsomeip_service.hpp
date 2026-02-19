#pragma once
#include <cstdint>
#include <memory>
#include <vsomeip/vsomeip.hpp>

class MotorHealthDiagnosticServiceService {
public:
    MotorHealthDiagnosticServiceService();
    bool init();
    void start();
    void stop();

    static constexpr uint16_t SERVICE_ID = 0x1201;
    static constexpr uint16_t INSTANCE_ID = 0x1;
    static constexpr uint16_t GETMOTORHEALTH_ID = 0x1;
    static constexpr uint16_t MOTORWARNING_ID = 0x8201;

private:
    std::shared_ptr<vsomeip::application> app_;
        void on_getmotorhealth(const std::shared_ptr<vsomeip::message>& request);
};
