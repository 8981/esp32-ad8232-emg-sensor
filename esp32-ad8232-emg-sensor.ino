//Configuration for 4 sensors
const int NUM_SENSORS = 4;

const int SENSOR_PINS[NUM_SENSORS] = {36, 39, 34, 35};
const int LO_PLUS_PINS[NUM_SENSORS] = {19, 21, 23, 26};
const int LO_MINUS_PINS[NUM_SENSORS] = {18, 22, 25, 27};

//Satus of each sensors
float dynOff[NUM_SENSORS] = {2048, 2048, 2048, 2048};
float envelope[NUM_SENSORS] = {0, 0, 0, 0};

//Filter 50Gh for each sensor
const float n_a1 = -1.7911f, n_a2 = 0.9803f;
const float n_b0 = 0.9901f, n_b1 = -1.7911f, n_b2 = 0.9901f;
float fx0[NUM_SENSORS] = {0}, fx1[NUM_SENSORS] = {0}, fx2[NUM_SENSORS] = {0};
float fy0[NUM_SENSORS] = {0}, fy1[NUM_SENSORS] = {0}, fy2[NUM_SENSORS] = {0}; 

static unsigned long lastT = 0;

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  setCpuFrequencyMhz(240);

  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(LO_PLUS_PINS[i], INPUT);
    pinMode(LO_MINUS_PINS[i], INPUT);
  }
}

void loop() {
  //Process each sensor
   for (int i = 0; i < NUM_SENSORS; i++) {
    float emgOut = 0;

    // Electrode contact check
    if (digitalRead(LO_PLUS_PINS[i]) || digitalRead(LO_MINUS_PINS[i])) {
      emgOut = 0;
      // Dropping
      dynOff[i] = 2048;
      envelope[i] = 0;
      fx0[i]=fx1[i]=fx2[i]=fy0[i]=fy1[i]=fy2[i]=0;
    } else {
      // Averaging ADCs
      int raw = 0;
      for (int j = 0; j < 4; j++) raw += analogRead(SENSOR_PINS[i]);
      raw >>= 2;

      // Dynamic centering
      dynOff[i] = dynOff[i] * 0.99f + raw * 0.01f;
      float centered = raw - dynOff[i];

      // Filter 50Gh
      fx2[i]=fx1[i]; fx1[i]=fx0[i]; fx0[i]=centered;
      fy2[i]=fy1[i]; fy1[i]=fy0[i];
      fy0[i] = n_b0*fx0[i] + n_b1*fx1[i] + n_b2*fx2[i] + n_a1*fy1[i] + n_a2*fy2[i];

      // Envelope (smooth)
      envelope[i] = 0.05f * fabs(fy0[i]) + 0.95f * envelope[i];
      emgOut = envelope[i] * 5;
    }

    // Comma-separated output
    Serial.print(emgOut);
    if (i < NUM_SENSORS - 1) Serial.print(",");
  }
  Serial.println();

  // Timing 500 Gh
  while (micros() - lastT < 2000UL);
  lastT = micros();
}