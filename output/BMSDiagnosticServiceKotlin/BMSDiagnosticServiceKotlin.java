import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BMSDiagnosticServiceKotlin {
    private static final Logger logger = LoggerFactory.getLogger(BMSDiagnosticServiceKotlin.class);
    
    public float[] GetBatteryStatus() {
        float soc = 20.5f;
        float voltage = 12.3f;
        float current = -1.2f;
        float temperature = 25f;
        int health_status = 1;
        
        checkBatteryWarning(soc, voltage, current, temperature);
        
        return new float[]{soc, voltage, current, temperature, health_status};
    }
    
    public float[] GetCellVoltages() {
        return new float[]{12.0f, 12.1f, 12.2f};
    }
    
    public float GetEstimatedRange(int driving_mode) {
        return 100.5f;
    }
    
    private void checkBatteryWarning(float soc, float voltage, float current, float temperature) {
        if (soc < 20) {
            logger.error("Low battery");
            throw new RuntimeException("Low battery");
        }
        
        if (temperature > 45) {
            logger.warn("High temperature");
            throw new RuntimeException("High temperature");
        }
        
        if (temperature > 60) {
            logger.error("Critical temperature - shutdown required");
            throw new RuntimeException("Critical temperature - shutdown required");
        }
    }
}