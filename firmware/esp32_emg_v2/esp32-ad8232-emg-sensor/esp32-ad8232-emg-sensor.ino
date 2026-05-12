// ===== EMG 3 sensors: v2 feature extraction for REST/FIST =====
// Output format:
// idx,m1,s1,a1,p1,m2,s2,a2,p2,m3,s3,a3,p3,label
//
// For each sensor:
// m = mean absolute value of centered signal
// s = standard deviation of centered signal
// a = signal activity / average power
// p = peak absolute value in the window

#include <Arduino.h>
#include <math.h>

const int NUM_SENSORS = 3;
const int SENSOR_PINS[NUM_SENSORS] = {36, 39, 34};

// Sampling: 500 Hz => 1 sample every 2000 microseconds
const uint32_t PERIOD_US = 2000UL;

// ADC averaging per sample
const int ADC_AVG = 4;

// Feature window: 25 samples * 2ms = 50ms => about 20 rows/sec
const int WINDOW_SAMPLES = 25;

// label: 0 = REST/open, 1 = FIST/closed, 2 = none
int label = 4;

// Dynamic offsets for centering signal
float dynOff[NUM_SENSORS] = {2048, 2048, 2048};

// Window accumulators
float sum[NUM_SENSORS] = {0, 0, 0};
float sumSq[NUM_SENSORS] = {0, 0, 0};
float sumAbs[NUM_SENSORS] = {0, 0, 0};
float peakAbs[NUM_SENSORS] = {0, 0, 0};

int winCnt = 0;

// Timing
uint32_t lastSampleT = 0;
uint32_t sampleIdx = 0;

void handleSerialLabel() {
  while (Serial.available()) {
    char c = (char)Serial.read();

    if (c == 'r' || c == 'R') {
      label = 0;
    } 
    else if (c == 'f' || c == 'F') {
      label = 1;
    }
    else if (c == 'u' || c == 'U') {
      label = 2;
    } 
    else if (c == 'd' || c == 'D') {
      label = 3;
    } 
    else if (c == 'n' || c == 'N') {
      label = 4;
    }
  }
}

void resetWindow() {
  winCnt = 0;

  for (int i = 0; i < NUM_SENSORS; i++) {
    sum[i] = 0;
    sumSq[i] = 0;
    sumAbs[i] = 0;
    peakAbs[i] = 0;
  }
}

void setup() {
  Serial.begin(115200);

  analogReadResolution(12);
  setCpuFrequencyMhz(240);

  lastSampleT = micros();

  Serial.println("idx,m1,s1,a1,p1,m2,s2,a2,p2,m3,s3,a3,p3,label");
}

void loop() {
  handleSerialLabel();

  // Wait for the next 2 ms tick
  while ((uint32_t)(micros() - lastSampleT) < PERIOD_US) {
    // busy wait
  }

  lastSampleT = micros();
  sampleIdx++;

  for (int i = 0; i < NUM_SENSORS; i++) {
    int raw = 0;

    for (int j = 0; j < ADC_AVG; j++) {
      raw += analogRead(SENSOR_PINS[i]);
    }

    raw /= ADC_AVG;

    // Dynamic baseline correction
    dynOff[i] = dynOff[i] * 0.99f + raw * 0.01f;

    float centered = (float)raw - dynOff[i];
    float absVal = fabs(centered);

    sum[i] += centered;
    sumSq[i] += centered * centered;
    sumAbs[i] += absVal;

    if (absVal > peakAbs[i]) {
      peakAbs[i] = absVal;
    }
  }

  winCnt++;

  if (winCnt >= WINDOW_SAMPLES) {
    Serial.print(sampleIdx);
    Serial.print(",");

    for (int i = 0; i < NUM_SENSORS; i++) {
      float mean = sum[i] / (float)winCnt;
      float meanAbs = sumAbs[i] / (float)winCnt;

      float variance = (sumSq[i] / (float)winCnt) - (mean * mean);
      if (variance < 0) {
        variance = 0;
      }

      float stdDev = sqrt(variance);

      // v2 features
      float m = meanAbs;                       // Mean Absolute Value
      float s = stdDev;                        // Standard Deviation
      float a = sumSq[i] / (float)winCnt;      // Signal Activity / Power
      float p = peakAbs[i];                    // Peak Absolute Value

      Serial.print(m, 3);
      Serial.print(",");
      Serial.print(s, 3);
      Serial.print(",");
      Serial.print(a, 3);
      Serial.print(",");
      Serial.print(p, 3);

      if (i < NUM_SENSORS - 1) {
        Serial.print(",");
      }
    }

    Serial.print(",");
    Serial.println(label);

    resetWindow();
  }
}