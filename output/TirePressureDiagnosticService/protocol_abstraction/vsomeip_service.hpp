#pragma once
#include <cstdint>
#include <memory>
#include <vsomeip/vsomeip.hpp>

class TirePressureDiagnosticServiceService {
public:
    TirePressureDiagnosticServiceService();
    bool init();
    void start();
    void stop();

    static constexpr uint16_t SERVICE_ID = 0x1101;
    static constexpr uint16_t INSTANCE_ID = 0x1;
    static constexpr uint16_t GETTIRESTATUS_ID = 0x1;
    static constexpr uint16_t TIREWARNING_ID = 0x8101;

private:
    std::shared_ptr<vsomeip::application> app_;
        void on_gettirestatus(const std::shared_ptr<vsomeip::message>& request);
};
