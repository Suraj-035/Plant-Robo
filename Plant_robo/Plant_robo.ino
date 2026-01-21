#include <Wire.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define I2C_ADDR_OLED 0x3C

Adafruit_SH1106G display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

#include <FluxGarage_RoboEyes.h>
#undef S

#include <DHT.h>
#include <LiquidCrystal_I2C.h>

// ================= EMOTIONS =================
enum Emotion { EMO_SAD, EMO_HAPPY, EMO_SUPER };
Emotion currentEmotion = EMO_SAD;
Emotion lastEmotion = EMO_SAD;

// ================= LCD =================
LiquidCrystal_I2C lcd(0x27, 16, 2);
unsigned long lastLCD = 0;

// ================= DHT11 =================
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// ================= SOIL SENSOR =================
#define SOIL_PWR 25
#define SOIL_PIN 34

// ================= TOUCH SENSORS =================
#define TOUCH_LEFT 12
#define TOUCH_RIGHT 13

// ================= FACE DETECTION =================
bool personDetected = false;
unsigned long lastSeenTime = 0;
const unsigned long HAPPY_HOLD_TIME = 5000;

// ================= TIMERS =================
unsigned long lastSensorRead = 0;
const unsigned long SENSOR_INTERVAL = 2000;

// ================= SENSOR VALUES =================
float temperature = 0;
float humidity = 0;
int soilPercent = 0;

// ================= ROBO EYES =================
roboEyes roboEyes;

// =================================================

void setup() {
  Serial.begin(115200);

  Wire.begin(21, 22);

  delay(200);
  display.begin(I2C_ADDR_OLED, true);

  roboEyes.begin(SCREEN_WIDTH, SCREEN_HEIGHT, 100);
  roboEyes.setAutoblinker(ON, 3, 2);
  roboEyes.setIdleMode(ON, 2, 2);
  roboEyes.setWidth(36, 36);
  roboEyes.setHeight(20, 20);
  roboEyes.setBorderradius(8, 8);
  roboEyes.setSpacebetween(20);

  lcd.init();
  delay(200);
  lcd.clear();
  lcd.backlight();

  dht.begin();

  pinMode(SOIL_PWR, OUTPUT);
  digitalWrite(SOIL_PWR, LOW);

  pinMode(TOUCH_LEFT, INPUT);
  pinMode(TOUCH_RIGHT, INPUT);

  lcd.setCursor(0, 0);
  lcd.print("Plant booting");
  lcd.setCursor(0, 1);
  lcd.print("...");
  delay(1500);
  lcd.clear();
}

// =================================================

void loop() {

  // ---- SERIAL FROM PYTHON ----
  if (Serial.available()) {
    char c = Serial.read();
    if (c == '1') {
      personDetected = true;
      lastSeenTime = millis();
    } 
    else if (c == '0') {
      personDetected = false;
    }
  }

  // ---- TOUCH ----
  bool touch = digitalRead(TOUCH_LEFT) || digitalRead(TOUCH_RIGHT);

  // ---- READ SENSORS ----
  if (millis() - lastSensorRead > SENSOR_INTERVAL) {
    lastSensorRead = millis();

    humidity = dht.readHumidity();
    temperature = dht.readTemperature(false);

    digitalWrite(SOIL_PWR, HIGH);
    delay(10);
    int soilRaw = analogRead(SOIL_PIN);
    digitalWrite(SOIL_PWR, LOW);

    soilPercent = map(soilRaw, 3500, 1500, 0, 100);
    soilPercent = constrain(soilPercent, 0, 100);
  }

  // ---- EMOTION LOGIC ----
  if (touch) {
    currentEmotion = EMO_SUPER;
  }
  else if (personDetected || (millis() - lastSeenTime < HAPPY_HOLD_TIME)) {
    currentEmotion = EMO_HAPPY;
  }
  else {
    currentEmotion = EMO_SAD;
  }

  // ---- EYES (CHANGE ONLY ON STATE CHANGE) ----
  if (currentEmotion != lastEmotion) {

    if (currentEmotion == EMO_SUPER) {
      roboEyes.setAutoblinker(OFF, 0, 0);
      roboEyes.setIdleMode(OFF, 0, 0);
      roboEyes.setMood(HAPPY);
      roboEyes.anim_laugh();
    }
    else if (currentEmotion == EMO_HAPPY) {
      roboEyes.setAutoblinker(ON, 3, 2);
      roboEyes.setIdleMode(ON, 2, 2);
      roboEyes.setMood(HAPPY);
    }
    else {
      roboEyes.setAutoblinker(ON, 4, 3);
      roboEyes.setIdleMode(ON, 3, 3);
      roboEyes.setMood(TIRED);
    }

    lastEmotion = currentEmotion;
  }

  roboEyes.update();

  // ---- LCD UPDATE (SLOW) ----
  if (millis() - lastLCD > 800) {
    lastLCD = millis();

    lcd.setCursor(0, 0);
    lcd.print("T:");
    lcd.print((int)temperature);
    lcd.print("C H:");
    lcd.print((int)humidity);
    lcd.print("% ");

    lcd.setCursor(0, 1);

    if (currentEmotion == EMO_SUPER) {
      lcd.print("I feel loved <3 ");
    }
    else if (soilPercent < 30) {
      lcd.print("I'm thirsty :( ");
    }
    else if (currentEmotion == EMO_HAPPY) {
      lcd.print("Hello human :) ");
    }
    else {
      lcd.print("All alone...   ");
    }
  }
}
