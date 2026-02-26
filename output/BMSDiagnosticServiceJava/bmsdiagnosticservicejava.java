import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BMSDiagnosticServiceJava {
    private static final Logger logger = LoggerFactory.getLogger(BMSDiagnosticServiceJava.class);

    public float GetBatteryStatus() {
        // Simulate getting battery status from some source
        BatteryStatus status = getBatteryStatusFromSource();
        
        if (status.getSoc() < 20) {
            throw new RuntimeException("Low battery");
        }
        
        if (status.getTemperature() > 45) {
            throw new RuntimeException("High temperature");
        }
        
        if (status.getTemperature() > 60) {
            throw new RuntimeException("Critical temperature - shutdown required");
        }
        
        return status.getSoc();
    }

    public float[] GetCellVoltages() {
        // Simulate getting cell voltages from some source
        return getCellVoltagesFromSource();
    }

    public float GetEstimatedRange(int driving_mode) {
        // Simulate getting estimated range based on driving mode
        return getEstimatedRangeFromSource(driving_mode);
    }

    private BatteryStatus getBatteryStatusFromSource() {
        // Placeholder for actual implementation
        return new BatteryStatus(25.0f, 420.0f, 10.0f, 30.0f, 1);
    }

    private float[] getCellVoltagesFromSource() {
        // Placeholder for actual implementation
        return new float[]{420.5f, 421.0f, 421.5f};
    }

    private float getEstimatedRangeFromSource(int driving_mode) {
        // Placeholder for actual implementation
        return 150.0f;
    }
}

class BatteryStatus {
    private float soc;
    private float voltage;
    private float current;
    private float temperature;
    private int health_status;

    public BatteryStatus(float soc, float voltage, float current, float temperature, int health_status) {
        this.soc = soc;
        this.voltage = voltage;
        this.current = current;
        this.temperature = temperature;
        this.health_status = health_status;
    }

    public float getSoc() {
        return soc;
    }

    public float getVoltage() {
        return voltage;
    }

    public float getCurrent() {
        return current;
    }

    public float getTemperature() {
        return temperature;
    }

    public int getHealthStatus() {
        return health_status;
    }
}