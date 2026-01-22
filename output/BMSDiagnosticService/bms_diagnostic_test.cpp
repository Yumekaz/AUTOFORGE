/**
 * AUTOFORGE - Adversarial Test Suite
 * BMS Diagnostic Service - Critical Alert Tests
 * 
 * Purpose: This test file is generated BEFORE the implementation
 * to define the expected behavior. The code generator must produce
 * code that passes ALL these tests.
 */

#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "bms_diagnostic_service.hpp"

namespace autoforge {
namespace bms {
namespace test {

// Test fixture for BMS Diagnostic Service
class BMSDiagnosticServiceTest : public ::testing::Test {
protected:
    void SetUp() override {
        service_ = std::make_unique<BMSDiagnosticService>();
        service_->Initialize();
    }

    void TearDown() override {
        service_->Shutdown();
    }

    std::unique_ptr<BMSDiagnosticService> service_;
};

/**
 * CRITICAL TEST: Battery Temperature Safety Threshold
 * 
 * Requirement: REQ-BMS-SAFETY-001
 * The system MUST trigger a CRITICAL alert when battery temperature
 * exceeds 60°C to prevent thermal runaway.
 * 
 * MISRA C++ Rule 0-1-1: All code shall conform to ISO C++
 */
TEST_F(BMSDiagnosticServiceTest, BatteryTemp_Critical_Alert_Above_60C) {
    // Arrange
    constexpr float CRITICAL_TEMP_THRESHOLD = 60.0f;
    constexpr float TEST_TEMP = 61.5f;  // Above critical threshold
    
    BatteryStatus status{};
    status.temperature_celsius = TEST_TEMP;
    status.state_of_charge = 75.0f;
    status.voltage = 400.0f;
    status.current = 50.0f;
    
    // Act
    AlertLevel alert = service_->EvaluateBatteryHealth(status);
    
    // Assert - MUST be CRITICAL, anything else is a FAILURE
    EXPECT_EQ(alert, AlertLevel::CRITICAL) 
        << "SAFETY VIOLATION: Temperature " << TEST_TEMP 
        << "°C exceeds threshold " << CRITICAL_TEMP_THRESHOLD 
        << "°C but alert level is not CRITICAL!";
}

/**
 * STRICT TEST: Exact threshold boundary
 * At exactly 60°C, should still be WARNING (not CRITICAL)
 */
TEST_F(BMSDiagnosticServiceTest, BatteryTemp_Warning_At_Exactly_60C) {
    BatteryStatus status{};
    status.temperature_celsius = 60.0f;  // Exactly at threshold
    status.state_of_charge = 75.0f;
    status.voltage = 400.0f;
    status.current = 50.0f;
    
    AlertLevel alert = service_->EvaluateBatteryHealth(status);
    
    EXPECT_EQ(alert, AlertLevel::WARNING)
        << "At exactly 60°C, alert should be WARNING, not CRITICAL";
}

/**
 * STRICT TEST: Low temperature should be NORMAL
 */
TEST_F(BMSDiagnosticServiceTest, BatteryTemp_Normal_Below_45C) {
    BatteryStatus status{};
    status.temperature_celsius = 35.0f;  // Normal operating temp
    status.state_of_charge = 80.0f;
    status.voltage = 400.0f;
    status.current = 30.0f;
    
    AlertLevel alert = service_->EvaluateBatteryHealth(status);
    
    EXPECT_EQ(alert, AlertLevel::NORMAL);
}

/**
 * EDGE CASE: Negative temperature (cold climate)
 */
TEST_F(BMSDiagnosticServiceTest, BatteryTemp_Warning_Below_Minus10C) {
    BatteryStatus status{};
    status.temperature_celsius = -15.0f;  // Very cold
    status.state_of_charge = 60.0f;
    status.voltage = 380.0f;
    status.current = 20.0f;
    
    AlertLevel alert = service_->EvaluateBatteryHealth(status);
    
    EXPECT_EQ(alert, AlertLevel::WARNING)
        << "Extremely cold temperatures should trigger WARNING for battery protection";
}

/**
 * CRITICAL TEST: Combined failure scenario
 * High temp + Low SoC = EMERGENCY
 */
TEST_F(BMSDiagnosticServiceTest, CombinedFailure_HighTemp_LowSoC_Emergency) {
    BatteryStatus status{};
    status.temperature_celsius = 65.0f;  // Critical temp
    status.state_of_charge = 5.0f;       // Critically low charge
    status.voltage = 350.0f;
    status.current = 100.0f;             // High current draw
    
    AlertLevel alert = service_->EvaluateBatteryHealth(status);
    
    EXPECT_EQ(alert, AlertLevel::EMERGENCY)
        << "Combined high temp + low SoC + high current should trigger EMERGENCY!";
}

}  // namespace test
}  // namespace bms
}  // namespace autoforge

// Main entry point
int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
