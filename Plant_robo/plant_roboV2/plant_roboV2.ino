#include <DHT.h>

// -------- Pins --------
#define DHTPIN 16    
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

#define SOIL_PWR 25
#define SOIL_PIN 34

#define TOUCH_LEFT 26
#define TOUCH_RIGHT 27

#define SOUND_PIN 35

// -------- Timers --------
unsigned long lastSend = 0;
unsigned long lastDHT  = 0;

// -------- DHT values --------
float temp = 0;
float hum  = 0;

void setup() {
  Serial.begin(115200);

  dht.begin();

  pinMode(SOIL_PWR, OUTPUT);
  digitalWrite(SOIL_PWR, LOW);

  pinMode(TOUCH_LEFT, INPUT_PULLUP);
  pinMode(TOUCH_RIGHT, INPUT_PULLUP);

  Serial.println("PLANT_PET_READY");
}

void loop() {

  // ===== DHT every 8 seconds (VERY SAFE) =====
  if (millis() - lastDHT > 8000) {
    lastDHT = millis();

    yield();

    float h = dht.readHumidity();
    float t = dht.readTemperature(false);

    yield();

    if (!isnan(h) && !isnan(t) && t > 0 && t < 50 && h >= 0 && h <= 100) {
      hum = h;
      temp = t;
    }
  }


  // ===== Send data every 800 ms =====
  if (millis() - lastSend > 800) {
    lastSend = millis();

    digitalWrite(SOIL_PWR, HIGH);
    delay(5);
    int soilRaw = analogRead(SOIL_PIN);
    digitalWrite(SOIL_PWR, LOW);

    int tL = digitalRead(TOUCH_LEFT);
    int tR = digitalRead(TOUCH_RIGHT);

    int soundVal = analogRead(SOUND_PIN);

    Serial.print("TEMP:"); Serial.print((int)temp);
    Serial.print(",HUM:"); Serial.print((int)hum);
    Serial.print(",SOILRAW:"); Serial.print(soilRaw);
    Serial.print(",TL:"); Serial.print(tL);
    Serial.print(",TR:"); Serial.print(tR);
    Serial.print(",SOUND:"); Serial.println(soundVal);
  }
}
