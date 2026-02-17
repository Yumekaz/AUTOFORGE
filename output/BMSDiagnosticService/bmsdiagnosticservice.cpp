#include <string>
#include <vector>
#include <cstdint>
#include <functional>
#include <iostream> // For basic logging, replace with actual logger in production
#include <algorithm> // For std::clamp
#include <cmath>     // For std::fabs, std::isnan, std::isinf

// MISRA C++: Rule A.3.1.1: The global namespace shall not be polluted.
// Use a dedicated namespace for the service.
namespace bms_diagnostic_service
{

// MISRA C++: Rule M.3.2.1: All declarations of an object or function shall use the same names and types for their parameters.
// MISRA C++: Rule