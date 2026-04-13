const int SENSOR_PIN = 36;
const int LO_MINUS = 18;
const int LO_PLUS = 19;

float filter_offset = 2048;
float envelope = 0;

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  pinMode(LO_MINUS, INPUT);
  pinMode(LO_PLUS, INPUT);
}

void loop() {
  if (digitalRead(LO_MINUS) == 1 || digitalRead(LO_PLUS) == 1) {
    Serial.println("0,0");
  } else {
    long sum = 0;
    for(int i = 0; i < 10; i++) sum += analogRead(SENSOR_PIN);
    float raw = sum / 10.0;

    filter_offset = (0.99 * filter_offset) + (0.01 * raw);
    float centered = raw - filter_offset;

    envelope = (0.05 * abs(centered)) + (0.95 * envelope);

    Serial.print(centered);
    Serial.print(",");
    Serial.println(envelope * 5);
  }

  delay(2);
}