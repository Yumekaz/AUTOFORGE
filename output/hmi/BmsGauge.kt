/**
 * AUTOFORGE - Android Automotive HMI
 * BmsGauge.kt - Battery State of Charge Gauge
 * 
 * Generated for: Vehicle Health Dashboard
 * Target: Android Automotive OS
 * Design: Dark theme, high contrast, driver-safe
 */

package com.autoforge.hmi.bms

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.car.app.CarContext
import androidx.car.app.Screen
import androidx.car.app.model.*
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

// ============================================================================
// Automotive Color Palette (High Contrast Dark Theme)
// ============================================================================
object AutomotiveColors {
    val Background = Color(0xFF0D0D0D)
    val Surface = Color(0xFF1A1A1A)
    val CardBackground = Color(0xFF252525)
    
    // Status Colors (High visibility for driver safety)
    val Critical = Color(0xFFFF3B3B)
    val Warning = Color(0xFFFFB800)
    val Normal = Color(0xFF00E676)
    val Info = Color(0xFF2196F3)
    
    // Gauge Colors
    val GaugeBackground = Color(0xFF333333)
    val GaugeGlow = Color(0xFF00E676).copy(alpha = 0.3f)
}

// ============================================================================
// BMS Data Model
// ============================================================================
data class BatteryStatus(
    val stateOfCharge: Float,        // 0-100%
    val temperatureCelsius: Float,
    val voltage: Float,
    val current: Float,
    val alertLevel: AlertLevel
)

enum class AlertLevel {
    NORMAL, WARNING, CRITICAL, EMERGENCY
}

// ============================================================================
// ViewModel with Real-time Data Observation
// ============================================================================
class BmsViewModel : ViewModel() {
    private val _batteryStatus = MutableStateFlow(
        BatteryStatus(
            stateOfCharge = 75f,
            temperatureCelsius = 35f,
            voltage = 400f,
            current = 45f,
            alertLevel = AlertLevel.NORMAL
        )
    )
    val batteryStatus: StateFlow<BatteryStatus> = _batteryStatus
    
    // LiveData alternative for legacy support
    private val _batteryLiveData = MutableLiveData<BatteryStatus>()
    val batteryLiveData: LiveData<BatteryStatus> = _batteryLiveData
    
    fun updateBatteryStatus(status: BatteryStatus) {
        _batteryStatus.value = status
        _batteryLiveData.value = status
    }
}

// ============================================================================
// Main Composable: BmsGauge
// ============================================================================
@Composable
fun BmsGauge(
    stateOfCharge: Float,
    alertLevel: AlertLevel,
    modifier: Modifier = Modifier
) {
    val animatedSoC by animateFloatAsState(
        targetValue = stateOfCharge,
        animationSpec = tween(durationMillis = 800, easing = FastOutSlowInEasing),
        label = "SoC Animation"
    )
    
    val gaugeColor = when (alertLevel) {
        AlertLevel.EMERGENCY -> AutomotiveColors.Critical
        AlertLevel.CRITICAL -> AutomotiveColors.Critical
        AlertLevel.WARNING -> AutomotiveColors.Warning
        AlertLevel.NORMAL -> AutomotiveColors.Normal
    }
    
    // Large touch target (min 48dp as per Android Automotive guidelines)
    Box(
        modifier = modifier
            .size(200.dp)  // Large for driver visibility
            .padding(16.dp),
        contentAlignment = Alignment.Center
    ) {
        // Background arc
        Canvas(modifier = Modifier.fillMaxSize()) {
            val strokeWidth = 20.dp.toPx()
            val radius = (size.minDimension - strokeWidth) / 2
            
            // Background track
            drawArc(
                color = AutomotiveColors.GaugeBackground,
                startAngle = 135f,
                sweepAngle = 270f,
                useCenter = false,
                topLeft = Offset(
                    (size.width - radius * 2) / 2,
                    (size.height - radius * 2) / 2
                ),
                size = Size(radius * 2, radius * 2),
                style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
            )
            
            // Foreground arc (SoC indicator)
            val sweepAngle = (animatedSoC / 100f) * 270f
            drawArc(
                brush = Brush.sweepGradient(
                    colors = listOf(gaugeColor.copy(alpha = 0.6f), gaugeColor)
                ),
                startAngle = 135f,
                sweepAngle = sweepAngle,
                useCenter = false,
                topLeft = Offset(
                    (size.width - radius * 2) / 2,
                    (size.height - radius * 2) / 2
                ),
                size = Size(radius * 2, radius * 2),
                style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
            )
        }
        
        // Center text (SoC percentage)
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = "${animatedSoC.toInt()}",
                fontSize = 48.sp,  // Large for driver readability
                fontWeight = FontWeight.Bold,
                color = gaugeColor
            )
            Text(
                text = "%",
                fontSize = 20.sp,
                color = Color.White.copy(alpha = 0.7f)
            )
            Text(
                text = "BATTERY",
                fontSize = 12.sp,
                color = Color.White.copy(alpha = 0.5f),
                letterSpacing = 2.sp
            )
        }
    }
}

// ============================================================================
// Vehicle Health Dashboard Screen
// ============================================================================
@Composable
fun VehicleHealthDashboard(viewModel: BmsViewModel = viewModel()) {
    val batteryStatus by viewModel.batteryStatus.collectAsState()
    
    Surface(
        modifier = Modifier.fillMaxSize(),
        color = AutomotiveColors.Background
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Header
            Text(
                text = "VEHICLE HEALTH",
                fontSize = 24.sp,
                fontWeight = FontWeight.Light,
                color = Color.White,
                letterSpacing = 4.sp
            )
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // Main Gauge
            BmsGauge(
                stateOfCharge = batteryStatus.stateOfCharge,
                alertLevel = batteryStatus.alertLevel,
                modifier = Modifier.size(240.dp)
            )
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Status Cards Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                StatusCard(
                    label = "TEMP",
                    value = "${batteryStatus.temperatureCelsius.toInt()}°C",
                    isWarning = batteryStatus.temperatureCelsius > 45f
                )
                StatusCard(
                    label = "VOLTAGE",
                    value = "${batteryStatus.voltage.toInt()}V",
                    isWarning = false
                )
                StatusCard(
                    label = "CURRENT",
                    value = "${batteryStatus.current.toInt()}A",
                    isWarning = batteryStatus.current > 80f
                )
            }
            
            // Alert Banner (if applicable)
            if (batteryStatus.alertLevel != AlertLevel.NORMAL) {
                Spacer(modifier = Modifier.height(24.dp))
                AlertBanner(alertLevel = batteryStatus.alertLevel)
            }
        }
    }
}

@Composable
fun StatusCard(
    label: String,
    value: String,
    isWarning: Boolean
) {
    Card(
        modifier = Modifier
            .size(width = 100.dp, height = 80.dp),  // Large touch target
        colors = CardDefaults.cardColors(
            containerColor = AutomotiveColors.CardBackground
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = label,
                fontSize = 10.sp,
                color = Color.White.copy(alpha = 0.5f),
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = value,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                color = if (isWarning) AutomotiveColors.Warning else Color.White
            )
        }
    }
}

@Composable
fun AlertBanner(alertLevel: AlertLevel) {
    val (color, message) = when (alertLevel) {
        AlertLevel.EMERGENCY -> AutomotiveColors.Critical to "⚠️ EMERGENCY: PULL OVER SAFELY"
        AlertLevel.CRITICAL -> AutomotiveColors.Critical to "⚠️ CRITICAL: SERVICE REQUIRED"
        AlertLevel.WARNING -> AutomotiveColors.Warning to "⚡ WARNING: CHECK BATTERY"
        AlertLevel.NORMAL -> AutomotiveColors.Normal to ""
    }
    
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),  // Large touch target
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.2f)),
        shape = RoundedCornerShape(8.dp)
    ) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = message,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                color = color
            )
        }
    }
}

// ============================================================================
// Activity Entry Point
// ============================================================================
class BmsGaugeActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    background = AutomotiveColors.Background,
                    surface = AutomotiveColors.Surface
                )
            ) {
                VehicleHealthDashboard()
            }
        }
    }
}
