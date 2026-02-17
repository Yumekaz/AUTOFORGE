import pytest
from unittest.mock import Mock, call
import math

# Define constants for clarity and MISRA compliance (avoiding magic numbers)
# These would typically be defined in a shared header or configuration file for the actual service.
BATTERY_SOC_LOW_WARNING_THRESHOLD = 20.0
BATTERY_TEMP_HIGH_WARNING_THRESHOLD = 45.0
BATTERY_TEMP_CRITICAL_SHUTDOWN_THRESHOLD = 60.0

HEALTH_STATUS_OK = 0
HEALTH_STATUS_WARNING = 1
HEALTH_STATUS_CRITICAL = 2

DRIVING_MODE_ECO = 0
DRIVING_MODE_NORMAL = 1
DRIVING_MODE_SPORT = 2