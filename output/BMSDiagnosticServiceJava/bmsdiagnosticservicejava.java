import java.util.HashMap;
import java.util.Map;

public class BMSDiagnosticServiceJava {
    private float battery_soc;
    private float battery_voltage;
    private float battery_current;
    private float battery_temperature;
    private int health_status;
    private List<Float> cell_voltages;
    private boolean isShutdownRequired = false;

    public Map<String, Object> GetBatteryStatus() {
        if (battery_soc < 20) {
            emitEvent(32769, new HashMap<String, Object>() {{
                put("warning_code", 0x0001);
                put("warning_message", "Low battery");
            }});
        }
        if (battery_temperature > 45) {
            emitEvent(32769, new HashMap<String, Object>() {{
                put("warning_code", 0x0002);
                put("warning_message", "High temperature");
            }});
        }
        if (battery_temperature > 60) {
            isShutdownRequired = true;
            emitEvent(32769, new HashMap<String, Object>() {{
                put("warning_code", 0x0003);
                put("warning_message", "Critical temperature - shutdown required");
            }});
        }
        Map<String, Object> status = new HashMap<>();
        status.put("soc", battery_soc);
        status.put("voltage", battery_voltage);
        status.put("current", battery_current);
        status.put("temperature", battery_temperature);
        status.put("health_status", health_status);
        return status;
    }

    public List<Float> GetCellVoltages() {
        return cell_voltages;
    }

    public Map<String, Object> GetEstimatedRange(int driving_mode) {
        // Placeholder for actual implementation
        Map<String, Object> range = new HashMap<>();
        range.put("range_km", 150.0);
        return range;
    }

    private void emitEvent(int eventId, Map<String, Object> fields) {
        try {
            some_module.emit_event(eventId, fields);
        } catch (Exception e) {
            // Handle exception
        }
    }

    public void setBatterySoc(float battery_soc) {
        this.battery_soc = battery_soc;
    }

    public void setBatteryVoltage(float battery_voltage) {
        this.battery_voltage = battery_voltage;
    }

    public void setBatteryCurrent(float battery_current) {
        this.battery_current = battery_current;
    }

    public void setBatteryTemperature(float battery_temperature) {
        this.battery_temperature = battery_temperature;
    }

    public void setHealthStatus(int health_status) {
        this.health_status = health_status;
    }

    public void setCellVoltages(List<Float> cell_voltages) {
        this.cell_voltages = cell_voltages;
    }
}