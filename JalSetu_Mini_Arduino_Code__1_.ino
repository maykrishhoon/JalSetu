/*
  ============================================================================
   JALSETU MINI — Benchtop Conjunctive Water-Allocation Demonstrator
  ============================================================================
   What this demonstrates (maps directly to the JalSetu project design docs):
     - Sensor A = "Canal / Tail-Chak Water Level"     -> real system: Doppler/radar sensor at a chak outlet
     - Sensor B = "Groundwater / Piezometer Level"     -> real system: pressure-transducer piezometer
     - Servo    = "Motorized Canal Gate Regulator"     -> real system: solar-powered gate actuator
     - Button   = "AUTO <-> MANUAL toggle"             -> real system: JE-level human-in-the-loop override
     - Potentiometer = "Manual gate position control"  -> real system: JE sets position from the GIS dashboard
     - LCD      = "Local status readout"               -> real system: JE dashboard summary tile

   CORE LOGIC (mirrors the conjunctive decision rule from the project docs):
     - If the canal/tail-chak level is LOW  -> open the gate proportionally more.
     - If groundwater is ALSO stressed (low) at the same time -> open the gate
       further still, representing "extend the release window" behaviour instead
       of letting farmers fall back on tubewell pumping.
     - A human (button) can always take over and set the gate directly with the
       potentiometer — the algorithm never has the only say.

   NOTE ON SENSORS: an HC-SR04 measures DISTANCE to whatever is in front of it.
     - LARGER distance reading  = surface is FAR from the sensor = LOW level.
     - SMALLER distance reading = surface is CLOSE to the sensor = HIGH level.
   For the live demo, just move your hand / a small card closer to or further
   from each sensor to simulate the water level rising and falling.
  ============================================================================
*/

#include <Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ---------------------------------------------------------------------------
// PIN MAP  (matches JalSetu_Wiring_Diagram.svg)
// ---------------------------------------------------------------------------
const int PIN_CANAL_TRIG   = 9;
const int PIN_CANAL_ECHO   = 8;
const int PIN_GW_TRIG      = 7;
const int PIN_GW_ECHO      = 6;
const int PIN_SERVO        = 10;
const int PIN_BUTTON       = 2;   // to GND, uses internal pull-up
const int PIN_POT          = A0;

// LCD address is usually 0x27 or 0x3F on most I2C backpacks.
// If the screen stays blank, try changing 0x27 to 0x3F below.
LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo gateServo;

// ---------------------------------------------------------------------------
// CALIBRATION — adjust these after a quick test run (see build guide, Step 5)
// ---------------------------------------------------------------------------
const int CANAL_DIST_FULL_CM  = 3;   // reading when "canal full" (hand close to sensor)
const int CANAL_DIST_EMPTY_CM = 20;  // reading when "canal empty" (hand far from sensor)
const int GW_STRESS_THRESHOLD_CM = 15; // beyond this distance = groundwater "stressed"

const int GATE_MIN_ANGLE = 15;   // servo angle = fully closed
const int GATE_MAX_ANGLE = 150;  // servo angle = fully open
const int GATE_STRESS_BOOST = 20; // extra degrees opened when groundwater is also stressed

// ---------------------------------------------------------------------------
// STATE
// ---------------------------------------------------------------------------
bool manualMode = false;
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_MS = 250;

int currentGateAngle = GATE_MIN_ANGLE;
unsigned long lastLcdUpdate = 0;

// ---------------------------------------------------------------------------
void setup() {
  Serial.begin(9600);

  pinMode(PIN_CANAL_TRIG, OUTPUT);
  pinMode(PIN_CANAL_ECHO, INPUT);
  pinMode(PIN_GW_TRIG, OUTPUT);
  pinMode(PIN_GW_ECHO, INPUT);
  pinMode(PIN_BUTTON, INPUT_PULLUP);

  gateServo.attach(PIN_SERVO);
  gateServo.write(currentGateAngle);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("JalSetu Mini");
  lcd.setCursor(0, 1);
  lcd.print("Booting...");
  delay(1200);
  lcd.clear();
}

// ---------------------------------------------------------------------------
// Reads one HC-SR04 sensor and returns distance in cm (0 if no echo).
// ---------------------------------------------------------------------------
long readDistanceCm(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 25000UL); // 25ms timeout ~ 4m range
  if (duration == 0) return 0;
  return duration / 58; // speed-of-sound conversion to cm
}

// ---------------------------------------------------------------------------
void loop() {
  // ---- 1. Handle manual/auto toggle button (debounced) ----
  int buttonState = digitalRead(PIN_BUTTON);
  if (buttonState == LOW && lastButtonState == HIGH &&
      (millis() - lastDebounceTime) > DEBOUNCE_MS) {
    manualMode = !manualMode;
    lastDebounceTime = millis();
    lcd.clear();
  }
  lastButtonState = buttonState;

  // ---- 2. Read sensors ----
  long canalDist = readDistanceCm(PIN_CANAL_TRIG, PIN_CANAL_ECHO);
  delay(15); // let the two ultrasonic bursts settle so they don't cross-talk
  long gwDist = readDistanceCm(PIN_GW_TRIG, PIN_GW_ECHO);

  bool gwStressed = (gwDist > GW_STRESS_THRESHOLD_CM);

  // ---- 3. Decide gate angle ----
  if (manualMode) {
    int potVal = analogRead(PIN_POT); // 0-1023
    currentGateAngle = map(potVal, 0, 1023, GATE_MIN_ANGLE, GATE_MAX_ANGLE);
  } else {
    // Map canal distance (empty->full) onto gate angle (open->closed).
    long clamped = constrain(canalDist, CANAL_DIST_FULL_CM, CANAL_DIST_EMPTY_CM);
    int baseAngle = map(clamped, CANAL_DIST_FULL_CM, CANAL_DIST_EMPTY_CM,
                         GATE_MIN_ANGLE, GATE_MAX_ANGLE);
    // Conjunctive logic: if groundwater is ALSO stressed, open further still.
    if (gwStressed) {
      baseAngle = min(GATE_MAX_ANGLE, baseAngle + GATE_STRESS_BOOST);
    }
    currentGateAngle = baseAngle;
  }

  gateServo.write(currentGateAngle);

  // ---- 4. Update LCD (every 400ms, not every loop, to avoid flicker) ----
  if (millis() - lastLcdUpdate > 400) {
    lastLcdUpdate = millis();
    lcd.setCursor(0, 0);
    lcd.print("C:");
    lcd.print(canalDist);
    lcd.print("cm GW:");
    lcd.print(gwDist);
    lcd.print("cm ");

    lcd.setCursor(0, 1);
    lcd.print("Gate:");
    int gatePct = map(currentGateAngle, GATE_MIN_ANGLE, GATE_MAX_ANGLE, 0, 100);
    lcd.print(gatePct);
    lcd.print("% ");
    lcd.print(manualMode ? "MANUAL " : (gwStressed ? "AUTO+GW " : "AUTO    "));
  }

  // ---- 5. Serial log (useful while calibrating, and as a live backup view) ----
  Serial.print("Canal(cm): "); Serial.print(canalDist);
  Serial.print("  GW(cm): "); Serial.print(gwDist);
  Serial.print("  GWstress: "); Serial.print(gwStressed ? "YES" : "no");
  Serial.print("  Gate(deg): "); Serial.print(currentGateAngle);
  Serial.print("  Mode: "); Serial.println(manualMode ? "MANUAL" : "AUTO");

  delay(120);
}