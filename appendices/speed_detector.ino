#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <HCSR04.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);
const int trigPin = 9;
const int echoPin = 10;
UltraSonicDistanceSensor sensor(trigPin, echoPin);
const int raspberryPiSignalPin = 6;
const float speedLimitKmhArduino = 30.0;

float previousDistanceCm = -1;
unsigned long previousTimeMs = 0;
float currentSpeedKmh = 0.0;

unsigned long lastSignalTimeMs = 0;
const unsigned long signalDebounceMs = 5000;

void setup() {
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Dist:         cm");
  lcd.setCursor(0, 1);
  lcd.print("Speed:        km/h");

  pinMode(raspberryPiSignalPin, OUTPUT);
  digitalWrite(raspberryPiSignalPin, LOW);

  Serial.begin(9600);
  Serial.println("Arduino Speed Detection Initialized.");
}

void loop() {
  float sumDistance = 0;
  int numReadings = 5;
  float validReadingsCount = 0;

  for (int i = 0; i < numReadings; i++) {
    float reading = sensor.measureDistanceCm();
    if (reading != -1 && reading <= 400) {
      sumDistance += reading;
      validReadingsCount++;
    }
    delay(10);
  }

  float currentDistanceCm;
  if (validReadingsCount > 0) {
    currentDistanceCm = sumDistance / validReadingsCount;
  } else {
    currentDistanceCm = -1;
  }

  unsigned long currentTimeMs = millis();

  lcd.setCursor(6, 0);
  lcd.print("       ");
  lcd.setCursor(6, 0);
  if (currentDistanceCm == -1) {
    lcd.print("OOR");
    currentSpeedKmh = 0;
  } else {
    lcd.print(currentDistanceCm, 1);
  }

  if (currentDistanceCm != -1 && previousDistanceCm != -1) {
    float deltaTimeSeconds = (currentTimeMs - previousTimeMs) / 1000.0;
    if (deltaTimeSeconds > 0.02) {
      float distanceChangeCm = previousDistanceCm - currentDistanceCm;
      float speed_cm_per_s = distanceChangeCm / deltaTimeSeconds;
      currentSpeedKmh = abs(speed_cm_per_s) * 0.036;

      lcd.setCursor(7, 1);
      lcd.print("       ");
      lcd.setCursor(7, 1);
      lcd.print(currentSpeedKmh, 1);

      if (currentSpeedKmh > speedLimitKmhArduino) {
        if (currentTimeMs - lastSignalTimeMs > signalDebounceMs) {
          Serial.print("Speeding detected! Speed: ");
          Serial.print(currentSpeedKmh);
          Serial.println(" km/h. Signaling Pi.");

          digitalWrite(raspberryPiSignalPin, HIGH);
          delay(500);
          digitalWrite(raspberryPiSignalPin, LOW);
          lastSignalTimeMs = currentTimeMs;
        }
      }
    }
  } else if (currentDistanceCm != -1 && previousDistanceCm == -1) {
    lcd.setCursor(7, 1);
    lcd.print("---");
    currentSpeedKmh = 0;
  } else {
    lcd.setCursor(7, 1);
    lcd.print("---");
    currentSpeedKmh = 0;
  }

  if (currentDistanceCm != -1) {
    previousDistanceCm = currentDistanceCm;
  } else {
    previousDistanceCm = -1;
  }
  previousTimeMs = currentTimeMs;

  delay(100);
}
