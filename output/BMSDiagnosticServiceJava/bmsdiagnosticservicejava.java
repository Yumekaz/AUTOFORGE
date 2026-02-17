import java.util.HashMap;
import java.util.Map;

public class BMSDiagnosticServiceJava {
    private static final int LOW_BATTERY_SOC = 20;
    private static final int HIGH_TEMP_WARNING_THRESHOLD = 45;
    private static final int CRITICAL_TEMP_SHUTDOWN_THRESHOLD = 60;

    public Map<String, Object> GetBatteryStatus() {
        Map<String, Object> status = new HashMap<>();
        // Simulated battery data
        status.put("soc", 25.0);
        status.put("voltage", 420.0);
        status.put("current", 10.0);
        status.put("temperature", 30.0);
        status.put("health_status", 1);

        checkBatteryStatus(status);
        return status;
    }

    public float[] GetCellVoltages() {
        // Simulated cell voltages
        return new float[]{420.5f, 421.0f, 421.5f};
    }

    public Map<String, Object> GetEstimatedRange(int driving_mode) {
        Map<String, Object> range = new HashMap<>();
        // Simulated estimated range
        range.put("range_km", 150.0);
        return range;
    }

    private void checkBatteryStatus(Map<String, Object> status) {
        double soc = (double) status.get("soc");
        double temperature = (double) status.get("temperature");

        if (soc < LOW_BATTERY_SOC) {
            emitEvent("BatteryWarning", 0x0001, "Low battery");
        }
        if (temperature > HIGH_TEMP_WARNING_THRESHOLD) {
            emitEvent("BatteryWarning", 0x0002, "High temperature");
        }
        if (temperature > CRITICAL_TEMP_SHUTDOWN_THRESHOLD) {
            throw new SystemExitException("Critical temperature - shutdown required");
        }
    }

    private void emitEvent(String eventName, int code, String message) {
        // Simulated event emission
        System.out.println(eventName + ": " + code + ", " + message);
    }

    public static class SystemExitException extends RuntimeException {
        public SystemExitException(String message) {
            super(message);
        }
    }
}