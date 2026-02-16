#ifndef BMS_DIAGNOSTIC_SERVICE_H
#define BMS_DIAGNOSTIC_SERVICE_H

#include <string>
#include <vector>
#include <cstdint>
#include <map>
#include <mutex> // For std::mutex
#include <algorithm> // For std::clamp

// Include common types, configuration, and logger
#include "bms_types.h"
#include "bms_config.h"
#include "bms_logger.h"

namespace bms {
namespace diagnostic {

// Interface for BatteryWarning event listener
// This allows the service to be decoupled from the actual SOME/IP event emission mechanism.
class IBatteryWarningEvent {
