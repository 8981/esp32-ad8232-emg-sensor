/* 
 * Project: ESP32 EMG Monitoring with AD8232
 * 
 * Hardware Connections:
 * AD8232 OUTPUT -> ESP32 GPIO 36 (VP)
 * AD8232 LO-    -> ESP32 GPIO 18
 * AD8232 LO+    -> ESP32 GPIO 19
 * GND           -> GND
 * 3.3V          -> 3V3
 */

const int SENSOR_PIN = 36;    // Analog Input (ADC1_CH0)
const int LO_MINUS = 18;      // Leads-off Detection Minus
const int LO_PLUS = 19;       // Leads-off Detection Plus

// Parameters for EMG Envelope calculation (Smoothing)
const int WINDOW_SIZE = 60;   // Moving average window size
int buffer[WINDOW_SIZE];
int bufferIndex = 0;

void setup() {
  // Initialize serial communication at 115200 baud
  Serial.begin(115200);
  
  // Configure Lead-off pins as inputs
  pinMode(LO_MINUS, INPUT); 
  pinMode(LO_PLUS, INPUT);
  
  // Set ESP32 ADC resolution to 12-bit (0-4095 range)
  analogReadResolution(12); 
}

void loop() {
  // 1. Check if electrodes are properly attached
  if (digitalRead(LO_MINUS) == 1 || digitalRead(LO_PLUS) == 1) {
    Serial.println("! --- Electrodes Disconnected --- !");
    delay(100);
  } else {
    // 2. Read raw analog signal from the sensor
    int rawValue = analogRead(SENSOR_PIN);
    
    // 3. DC Offset Removal (Center the signal around 0)
    // ESP32 3.3V center is approximately 2048
    int centered = rawValue - 2048;

    // 4. Calculate Muscle Envelope (Signal Rectification & Averaging)
    buffer[bufferIndex] = abs(centered); // Full-wave rectification
    bufferIndex = (bufferIndex + 1) % WINDOW_SIZE;

    long sum = 0;
    for (int i = 0; i < WINDOW_SIZE; i++) {
      sum += buffer[i];
    }
    float emgStrength = sum / (float)WINDOW_SIZE;

    // 5. Output to Serial Plotter (Ctrl+Shift+L in Arduino IDE)
    Serial.print("Raw:");
    Serial.print(centered);
    Serial.print(",");
    Serial.print("MuscleStrength:");
    Serial.println(emgStrength * 3); // Gain multiplier for better visualization
  }

  // Adjust delay for plotter refresh rate (ms)
  delay(50); 
}