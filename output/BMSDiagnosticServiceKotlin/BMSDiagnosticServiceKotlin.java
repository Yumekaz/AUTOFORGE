import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BMSDiagnosticServiceKotlin {
    private static final Logger logger = LoggerFactory.getLogger(BMSDiagnosticServiceKotlin.class);
    private float batterySOC;
    private float batteryVoltage;
    private float batteryCurrent;
    private float batteryTemperature;
    private byte healthStatus;

    public BMSDiagnosticServiceKotlin(float batterySOC, float batteryVoltage, float batteryCurrent, float batteryTemperature, byte healthStatus) {
        this.batterySOC = batterySOC;
        this.batteryVoltage = batteryVoltage;
        this.batteryCurrent = batteryCurrent;
        this.batteryTemperature = batteryTemperature;
        this.healthStatus = healthStatus;
    }

    public Map<String, Object> GetBatteryStatus() throws Exception {
        if (batterySOC < 20) {
            throw new Exception("Low battery");
        }
        return Map.of(
                "soc", batterySOC,
                "voltage", batteryVoltage,
                "current", batteryCurrent,
                "temperature", batteryTemperature,
                "health_status", healthStatus
        );
    }

    public Map<String, Object> GetCellVoltages() {
        // Implement logic to get cell voltages
        return Map.of("cell_voltages", new float[]{3.7f, 3.8f, 3.9f});
    }

    public Map<String, Object> GetEstimatedRange(int drivingMode) {
        // Implement logic to estimate range based on driving mode
        return Map.of("range_km", 200.0f);
    }
}