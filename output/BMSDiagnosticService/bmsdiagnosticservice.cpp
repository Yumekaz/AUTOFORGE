#include <cstdint>
#include <string>
#include <vector>
#include <someip/someip.hpp>

class BatteryManagementSystem {
public:
    void set_battery_soc(float soc) { battery_soc_ = soc; }
    void set_battery_voltage(float voltage) { battery_voltage_ = voltage; }
    void set_battery_current(float current) { battery_current_ = current; }
    void set_battery_temperature(float temperature) { battery_temperature_ = temperature; }

    someip::message get_battery_status() const {
        someip::message msg;
        msg.set_service(4097);
        msg.set_instance(1);
        msg.set_method(1);
        msg.set_payload(create_payload());
        return msg;
    }

    someip::message get_cell_voltages() const {
        someip::message msg;
        msg.set_service(4097);
        msg.set_instance(1);
        msg.set_method(2);
        msg.set_payload({});
        return msg;
    }

    someip::message get_estimated_range(uint8_t driving_mode) const {
        someip::message msg;
        msg.set_service(4097);
        msg.set_instance(1);
        msg.set_method(3);
        msg.set_payload(create_payload(driving_mode));
        return msg;
    }

private:
    float battery_soc_ = 0.0f;
    float battery_voltage_ = 0.0f;
    float battery_current_ = 0.0f;
    float battery_temperature_ = 0.0f;

    std::vector<uint8_t> create_payload(uint8_t driving_mode = 1) const {
        someip::payload payload;
        payload.reserve(24);
        payload.push_back(static_cast<uint8_t>(battery_soc_));
        payload.push_back(static_cast<uint8_t>(battery_voltage_ / 256.0f));
        payload.push_back(static_cast<uint8_t>(battery_voltage_ % 256.0f));
        payload.push_back(static_cast<uint8_t>(battery_current_));
        payload.push_back(static_cast<uint8_t>(battery_temperature_));
        payload.push_back(driving_mode);
        return payload;
    }
};

int main() {
    BatteryManagementSystem bms;
    bms.set_battery_soc(50.0f);
    bms.set_battery_voltage(420.0f);
    bms.set_battery_current(10.0f);
    bms.set_battery_temperature(30.0f);

    someip::message status_msg = bms.get_battery_status();
    someip::message cell_voltages_msg = bms.get_cell_voltages();
    someip::message estimated_range_msg = bms.get_estimated_range(1);

    return 0;
}