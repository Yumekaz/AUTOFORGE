#include <cstdint>
#include <vector>
#include <string>
#include <memory>
#include <algorithm>
#include <iostream>
#include <stdexcept> // For std::runtime_error, used sparingly for critical internal errors
#include <cmath>     // For std::fabs

// MISRA C++ 2012 Rule 0-1-2: The value of an object with a non-trivial constructor or destructor shall not be used before it has been initialized.
// All member variables are initialized in the constructor initializer list.

// MISRA C++ 2012 Rule 0-1-4: A pointer or reference shall not be used unless it has been initialized.
// Smart pointers