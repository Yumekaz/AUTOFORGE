#include <vsomeip/vsomeip.hpp>
#include <iostream>

int main() {
    auto app = vsomeip::runtime::get()->create_application("BMSDiagnosticServiceJava_client");
    if (!app || !app->init()) {
        std::cerr << "Failed to init vsomeip client\n";
        return 1;
    }
    std::cout << "[ABSTRACTION] SOME/IP client skeleton ready for service "
              << "BMSDiagnosticServiceJava" << "\n";
    return 0;
}
