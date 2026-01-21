#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>


#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define OLED_ADDR 0x3C

Adafruit_SH1106G display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);


extern Adafruit_SH1106G display;

#include <FluxGarage_RoboEyes.h>


#undef N
#undef NE
#undef E
#undef SE
#undef S
#undef SW
#undef W
#undef NW

#include <DHT.h>


roboEyes roboEyes;


#define DHTPIN 16
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

#define SOIL_PWR 25
#define SOIL_PIN 34

#define TOUCH_LEFT 26
#define TOUCH_RIGHT 27

#define SOUND_PIN 35

bool showIntro = false;
unsigned long introStart = 0;


// ================= TIMERS =================
unsigned long lastSend = 0;
unsigned long lastDHT  = 0;

// ================= VALUES =================
float temp = 0;
float hum  = 0;

String currentMood = "NEUTRAL";


// ================= SETUP =================
void setup() {
  Serial.begin(115200);

  Wire.begin(21, 22);
  delay(300);

  display.begin(OLED_ADDR, true);
  display.clearDisplay();
  display.display();

  // ----- Robo Eyes Init -----
  roboEyes.begin(SCREEN_WIDTH, SCREEN_HEIGHT, 60);

  roboEyes.setAutoblinker(ON, 3, 2);
  roboEyes.setIdleMode(ON, 2, 2);

  // BIGGER EYES (you wanted bigger)
  roboEyes.setWidth(42, 42);
  roboEyes.setHeight(28, 28);
  roboEyes.setBorderradius(10, 10);
  roboEyes.setSpacebetween(18);

  roboEyes.setMood(DEFAULT);

  // ----- Sensors -----
  dht.begin();

  pinMode(SOIL_PWR, OUTPUT);
  digitalWrite(SOIL_PWR, LOW);

  pinMode(TOUCH_LEFT, INPUT_PULLUP);
  pinMode(TOUCH_RIGHT, INPUT_PULLUP);

  Serial.println("PLANT_PET_READY");
}

// ================= LOOP =================
void loop() {

  // ===== INTRO MODE =====
  if (showIntro) {
  if (millis() - introStart < 3000) {
    return;  // keep showing intro
  } else {
    showIntro = false;
    display.clearDisplay();
    display.display();   // now allow eyes to draw
  }
}


  roboEyes.update();

  // ===== SERIAL COMMANDS FROM PYTHON =====
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    // ---- INTRO ----
  if (cmd == "INTRO") {
    display.clearDisplay();
    display.setTextSize(2);
    display.setTextColor(SH110X_WHITE);
    display.setCursor(10,18);
    display.print("HI, I AM");
    display.setCursor(38,42);
    display.print("EVE");
    display.display();

    showIntro = true;
    introStart = millis();
    return;
  }

    // ---- MOOD ----
    if (cmd.startsWith("MOOD:")) {
      currentMood = cmd.substring(5);

      if (currentMood == "HAPPY") roboEyes.setMood(HAPPY);
      else if (currentMood == "ANGRY") roboEyes.setMood(ANGRY);
      else if (currentMood == "TIRED") roboEyes.setMood(TIRED);
      else roboEyes.setMood(DEFAULT);
    }

    // ---- EVENTS ----
    if (cmd == "EVENT:LAUGH") {
      roboEyes.anim_laugh();
    }

    if (cmd == "EVENT:SAD") {
      roboEyes.anim_confused();
    }
  }

  // ===== DHT EVERY 8s =====
  if (millis() - lastDHT > 8000) {
    lastDHT = millis();

    float h = dht.readHumidity();
    float t = dht.readTemperature(false);

    if (!isnan(h) && !isnan(t) && t > 0 && t < 60 && h >= 0 && h <= 100) {
      hum = h;
      temp = t;
    }
  }

  // ===== SEND SENSOR DATA =====
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
