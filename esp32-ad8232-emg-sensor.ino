// ===== EMG 3 sensors: stable feature extraction for rest/fist (NO notch) =====

const int NUM_SENSORS = 3;
const int SENSOR_PINS[NUM_SENSORS] = {36, 39, 34};

// Sampling: 500 Hz
const uint32_t PERIOD_US = 2000UL;

// ADC averaging
const int ADC_AVG = 4;

// Feature window: 25 samples * 2ms = 50ms => ~20 rows/sec
const int WINDOW_SAMPLES = 25;

// label: 0 rest, 1 fist, 2 none
int label = 2;

// Dynamic offsets
float dynOff[NUM_SENSORS] = {2048, 2048, 2048};

// Window accumulators
float sumAbs[NUM_SENSORS] = {0, 0, 0};
int winCnt = 0;

// Timing
uint32_t lastSampleT = 0;
uint32_t sampleIdx = 0;

void handleSerialLabel() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == 'r' || c == 'R') label = 0;
    else if (c == 'f' || c == 'F') label = 1;
    else if (c == 'n' || c == 'N') label = 2;
  }
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  setCpuFrequencyMhz(240);

  lastSampleT = micros();
  Serial.println("idx,featAbs1,featAbs2,featAbs3,label");
}

void loop() {
  handleSerialLabel();

  // wait next 2ms tick
  while ((uint32_t)(micros() - lastSampleT) < PERIOD_US) {}
  lastSampleT = micros();

  sampleIdx++;

  // acquire + dynamic centering + abs
  for (int i = 0; i < NUM_SENSORS; i++) {
    int raw = 0;
    for (int j = 0; j < ADC_AVG; j++) raw += analogRead(SENSOR_PINS[i]);
    raw /= ADC_AVG;

    dynOff[i] = dynOff[i] * 0.99f + raw * 0.01f;
    float centered = (float)raw - dynOff[i];

    sumAbs[i] += fabs(centered);
  }

  winCnt++;

  // every window print features
  if (winCnt >= WINDOW_SAMPLES) {
    float feat1 = sumAbs[0] / (float)winCnt;
    float feat2 = sumAbs[1] / (float)winCnt;
    float feat3 = sumAbs[2] / (float)winCnt;

    // печать ТОЛЬКО числа + label (без текста)
    Serial.print(sampleIdx); Serial.print(",");
    Serial.print(feat1, 3); Serial.print(",");
    Serial.print(feat2, 3); Serial.print(",");
    Serial.print(feat3, 3); Serial.print(",");
    Serial.println(label);

    winCnt = 0;
    sumAbs[0] = sumAbs[1] = sumAbs[2] = 0;
  }
}