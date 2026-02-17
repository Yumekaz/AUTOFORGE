import com.vsomeip.vsomeip;
import com.vsomeip.vsomeip.annotation.*;
import com.vsomeip.vsomeip.message.MessageType;
import com.vsomeip.vsomeip.service.ServiceID;
import com.vsomeip.vsomeip.service.InstanceID;
import com.vsomeip.vsomeip.service.MethodID;
import com.vsomeip.vsomeip.service.EventID;

@Service(
    service_id = ServiceID.of(4097),
    instance_id = InstanceID.of(1)
)
public class BMSDiagnosticServiceJava {

    private Application application;
    private final Event batteryWarningEvent;
    private final Method getBatteryStatusMethod;
    private final Method getCellVoltagesMethod;
    private final Method getEstimatedRangeMethod;

    public BMSDiagnosticServiceJava() {
        this.application = vsomeip.ApplicationFactory.getApplication("BMSDiagnosticServiceJava");
        
        this.batteryWarningEvent = application.createEvent(EventID.of(32769), EventGroupID.of(0));
        this.batteryWarningEvent.setUnreliable(true);
        this.batteryWarningEvent.setMulticast(false);

        this.getBatteryStatusMethod = application.createMethod(MethodID.of(1));
        this.getCellVoltagesMethod = application.createMethod(MethodID.of(2));
        this.getEstimatedRangeMethod = application.createMethod(MethodID.of(3));

        this.application.registerService();
        this.application.offerService(ServiceID.of(4097), InstanceID.of(1));
        this.application.offerEvent(EventID.of(32769), EventGroupID.of(0));
        
        this.application.registerEventHandler(EventID.of(32769), this::handleBatteryWarning);
    }

    @Message(
        id = MethodID.of(1),
        type = MessageType.REQUEST
    )
    public void onGetBatteryStatusRequest(Message request) {
        try {
            BatteryStatus batteryStatus = getBatteryStatus();
            application.sendEvent(batteryWarningEvent, request.get_client(), batteryStatus);
        } catch (Exception e) {
            handleException(e);
        }
    }

    @Message(
        id = MethodID.of(2),
        type = MessageType.REQUEST
    )
    public void onGetCellVoltagesRequest(Message request) {
        try {
            float[] cellVoltages = getCellVoltages();
            application.sendResponse(request, cellVoltages);
        } catch (Exception e) {
            handleException(e);
        }
    }

    @Message(
        id = MethodID.of(3),
        type = MessageType.REQUEST
    )
    public void onGetEstimatedRangeRequest(Message request, byte driving_mode) {
        try {
            float range_km = getEstimatedRange(driving_mode);
            application.sendResponse(request, range_km);
        } catch (Exception e) {
            handleException(e);
        }
    }

    private BatteryStatus getBatteryStatus() {
        // Simulate battery status retrieval
        BatteryStatus batteryStatus = new BatteryStatus();
        batteryStatus.setSoc(0.5f);
        batteryStatus.setVoltage(12.6f);
        batteryStatus.setCurrent(-3.4f);
        batteryStatus.setTemperature(28.0f);
        batteryStatus.setHealthStatus((byte) 1);

        // Check for warnings
        if (batteryStatus.getSoc() < 20) {
            emitBatteryWarning(0x0001, "Low battery");
        }
        if (batteryStatus.getTemperature() > 45) {
            emitBatteryWarning(0x0002, "High temperature");
        }
        if (batteryStatus.getTemperature() > 60) {
            emitBatteryWarning(0x0003, "Critical temperature - shutdown required");
        }

        return batteryStatus;
    }

    private float[] getCellVoltages() {
        // Simulate cell voltages retrieval
        return new float[]{3.7f, 3.8f, 3.9f};
    }

    private float getEstimatedRange(byte driving_mode) {
        // Simulate estimated range calculation
        return 200.5f;
    }

    private void emitBatteryWarning(int code, String message) {
        BatteryWarning warning = new BatteryWarning();
        warning.setCode(code);
        warning.setMessage(message);

        application.sendEvent(batteryWarningEvent, null, warning);
    }

    private void handleException(Exception e) {
        System.err.println("Error: " + e.getMessage());
        System.exit(1);
    }
}

class BatteryStatus {
    private float soc;
    private float voltage;
    private float current;
    private float temperature;
    private byte health_status;

    public float getSoc() {
        return soc;
    }

    public void setSoc(float soc) {
        this.soc = soc;
    }

    public float getVoltage() {
        return voltage;
    }

    public void setVoltage(float voltage) {
        this.voltage = voltage;
    }

    public float getCurrent() {
        return current;
    }

    public void setCurrent(float current) {
        this.current = current;
    }

    public float getTemperature() {
        return temperature;
    }

    public void setTemperature(float temperature) {
        this.temperature = temperature;
    }

    public byte getHealthStatus() {
        return health_status;
    }

    public void setHealthStatus(byte health_status) {
        this.health_status = health_status;
    }
}

class BatteryWarning {
    private int code;
    private String message;

    public int getCode() {
        return code;
    }

    public void setCode(int code) {
        this.code = code;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}