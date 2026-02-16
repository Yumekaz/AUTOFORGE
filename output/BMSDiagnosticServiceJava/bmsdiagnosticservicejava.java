import com.visteon.someip.client.SomeIPClient;
import com.visteon.someip.event.EventEmitter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BMSDiagnosticServiceJava {
    private static final Logger logger = LoggerFactory.getLogger(BMSDiagnosticServiceJava.class);
    private SomeIPClient someIPClient;
    private EventEmitter<BatteryWarning> batteryWarningEmitter;

    public BMSDiagnosticServiceJava(SomeIPClient someIPClient, EventEmitter<BatteryWarning> batteryWarningEmitter) {
        this.someIPClient = someIPClient;
        this.batteryWarningEmitter = batteryWarningEmitter;
    }

    public float GetBatteryStatus() {
        try {
            Object[] response = someIPClient.getMethod(1).invoke();
            float soc = (float) response[0];
            float voltage = (float) response[1];
            float current = (float) response[2];
            float temperature = (float) response[3];
            int healthStatus = (int) response[4];

            if (soc < 20) {
                batteryWarningEmitter.emit(new BatteryWarning(0x0001, "Low battery"));
            }
            if (temperature > 60) {
                throw new SystemExit("Critical temperature - shutdown required");
            } else if (temperature > 45) {
                batteryWarningEmitter.emit(new BatteryWarning(0x0002, "High temperature"));
            }

            return soc;
        } catch (Exception e) {
            logger.error("Error getting battery status", e);
            throw new RuntimeException("Failed to get battery status", e);
        }
    }

    public float[] GetCellVoltages() {
        try {
            Object[] response = someIPClient.getMethod(2).invoke();
            return (float[]) response[0];
        } catch (Exception e) {
            logger.error("Error getting cell voltages", e);
            throw new RuntimeException("Failed to get cell voltages", e);
        }
    }

    public float GetEstimatedRange(int drivingMode) {
        try {
            Object[] response = someIPClient.getMethod(3).invoke(drivingMode);
            return (float) response[0];
        } catch (Exception e) {
            logger.error("Error getting estimated range", e);
            throw new RuntimeException("Failed to get estimated range", e);
        }
    }

    public static class BatteryWarning {
        private int code;
        private String message;

        public BatteryWarning(int code, String message) {
            this.code = code;
            this.message = message;
        }

        // Getters and setters
    }
}