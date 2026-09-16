# JalSetu Mini — Benchtop Prototype Build Guide

A working tabletop demonstrator of JalSetu's core logic: two sensors (canal level + groundwater level) feed a decision loop that proportionally opens a gate — with a human override always available. No real water needed; you simulate level changes by moving your hand or a small card in front of each sensor.

**Budget:** ~₹900–1,300 · **Build time:** ~1–2 hours once parts arrive · **Skill level:** beginner Arduino

---

## 1 | What This Demonstrates

| Prototype part | Stands in for (from the JalSetu design docs) |
| :--- | :--- |
| Ultrasonic Sensor A | Doppler flow/level sensor at a tail-chak outlet |
| Ultrasonic Sensor B | Pressure-transducer piezometer (groundwater) |
| Servo + paper flap | Solar-powered motorized canal gate regulator |
| Push button | JE-level human-in-the-loop AUTO/MANUAL toggle |
| Potentiometer | JE manually setting gate position from the dashboard |
| 16×2 LCD | The at-a-glance summary tile on the GIS dashboard |

**The one thing worth rehearsing live:** move your hand close to Sensor A (canal "full") while holding your other hand far from Sensor B (groundwater "stressed"). A naive single-sensor system would leave the gate closed here — but JalSetu Mini opens it partway anyway, because the conjunctive logic reacts to the groundwater signal even when the canal alone looks fine. That's the entire pitch of the project in one live, physical moment.

---

## 2 | Bill of Materials

| # | Component | Approx. Price (₹) | Notes |
| :--- | :--- | :--- | :--- |
| 1 | Arduino Uno (or compatible clone) | 350–500 | Any Uno R3 clone works fine |
| 2 | HC-SR04 Ultrasonic Sensor | 60–90 each (×2 = 120–180) | Non-contact — matches the real radar/Doppler sensor story |
| 3 | SG90 Micro Servo Motor | 120–180 | The "gate actuator" |
| 4 | 16×2 LCD with I2C backpack | 150–220 | The I2C backpack means only 4 wires, not 16 |
| 5 | Push button (momentary) | 5–10 | Manual/Auto toggle |
| 6 | 10kΩ Potentiometer | 20–30 | Manual gate position dial |
| 7 | Breadboard (full-size) | 100–150 | |
| 8 | Jumper wires (M-M, M-F pack) | 100–150 | |
| 9 | USB cable (for Arduino) + power bank or laptop | usually on hand | Power source for the demo |
| 10 | Small cardboard/foam board + paper flap + glue | ~50 | For the visible "gate" and mounting |

**Where to buy:** Robu.in and Amazon.in both stock every part above individually; Robu.in is a well-known India-based electronics retailer that's usually faster for this category than general marketplaces. **Standard shipping typically takes 2–3 days** — if your meeting is sooner than that, check a local electronics market first, since waiting on delivery is the single biggest risk to this plan.

---

## 3 | Wiring

Full diagram: **`JalSetu_Wiring_Diagram.svg`** (shared alongside this guide). Pin table for quick reference while wiring:

| Component pin | Arduino pin |
| :--- | :--- |
| Sensor A (Canal) — TRIG | D9 |
| Sensor A (Canal) — ECHO | D8 |
| Sensor B (Groundwater) — TRIG | D7 |
| Sensor B (Groundwater) — ECHO | D6 |
| Servo — Signal | D10 |
| Push Button — one leg | D2 (other leg → GND) |
| Potentiometer — wiper (middle pin) | A0 |
| LCD (I2C) — SDA | A4 |
| LCD (I2C) — SCL | A5 |
| All VCC pins (sensors, servo, LCD, pot outer leg) | 5V rail |
| All GND pins (sensors, servo, LCD, pot outer leg, button) | GND rail |

> Use the breadboard's red/blue power rails for the shared 5V and GND connections — it keeps the wiring far less messy than running individual wires from the Arduino for every part.

---

## 4 | Software Setup

1. Install the **Arduino IDE** (arduino.cc/en/software) if you don't have it.
2. Open **Tools → Manage Libraries**, and install:
   - `Servo` (usually pre-installed)
   - `LiquidCrystal_I2C` by Frank de Brabander
3. Plug in the Arduino via USB, select the correct **Board** and **Port** under Tools.
4. Paste in the code from **Section 6** below, or open the attached `jalsetu_mini.ino` file directly.
5. Click **Upload**.

If the LCD stays blank after upload, it's almost always the I2C address — run **File → Examples → Wire → i2c_scanner**, note the address it prints (commonly `0x27` or `0x3F`), and update that value near the top of the code.

---

## 5 | Calibration (do this once, before the meeting)

The sensors return a *distance* reading — larger number means the "water" surface is farther away (lower level); smaller number means it's closer (higher level).

1. Upload the code and open **Tools → Serial Monitor** (9600 baud).
2. Hold your hand very close to Sensor A (simulating "canal full") and note the printed `Canal(cm)` value.
3. Hold your hand far away (simulating "canal empty") and note that value too.
4. In the code, set `CANAL_DIST_FULL_CM` and `CANAL_DIST_EMPTY_CM` to what you actually measured.
5. Repeat for Sensor B if you want tighter calibration, and adjust `GW_STRESS_THRESHOLD_CM` to a distance that's clearly "far" for your setup.
6. Re-upload after any changes.

---

## 6 | Full Arduino Code

```cpp
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
```

This exact logic was independently tested against five scenarios before being handed to you — including the "canal fine but groundwater stressed" case that produces the demo's key moment (gate opens to ~14% instead of staying at 0%, purely from the groundwater signal).

---

## 7 | Live Demo Script (about 90 seconds)

1. **"This is the sensor-to-actuation loop from JalSetu, running standalone."** Point to Sensor A: *"This represents a Doppler sensor at a tail-chak outlet."* Point to Sensor B: *"This represents a groundwater piezometer."*
2. Move your hand close to Sensor A. **"Canal's full — watch the gate."** Gate closes, LCD shows `AUTO`, low %.
3. Move your hand away from Sensor A. **"Now the canal's running dry."** Gate opens proportionally — not snapping fully open, matching the real system's *proportional* setpoint logic, not a blunt on/off valve.
4. **The key moment:** hand close to Sensor A (canal fine) **and** far from Sensor B (groundwater stressed) at the same time. **"Canal alone looks fine — but the aquifer's stressed. A single-sensor system would do nothing here. JalSetu doesn't wait for the canal to fail — it reacts to the aquifer signal directly."** LCD shows `AUTO+GW`, gate opens partway.
5. Press the button. **"And a human can always take over."** Turn the potentiometer — gate follows your hand directly. **"This is the JE engineer's override from the dashboard — the algorithm never has the only say."**
6. Press the button again to hand control back to AUTO.

---

## 8 | Troubleshooting

| Symptom | Likely fix |
| :--- | :--- |
| LCD blank / shows boxes only | Wrong I2C address — run the i2c_scanner sketch, update the address in code |
| Servo jitters constantly | Sensor picking up a wobbly/angled surface — point it at something flat, or increase `delay(120)` slightly |
| Both sensors interfere with each other | The 15ms gap between readings in the code should prevent this; if it persists, increase that delay to 30–50ms |
| Nothing powers on | Try a different USB cable — many only carry power, not data |
| Gate direction feels "backwards" | Swap `GATE_MIN_ANGLE`/`GATE_MAX_ANGLE` values |

---

## 9 | Connecting It Back to the Full System

Keep this framing ready for the Q&A: *"This benchtop version uses simple threshold logic because it has no history to learn from. The full-scale JalSetu replaces this loop's brain with the LSTM forecasting model from Assignment 3B — same sensor-to-actuation shape, but predicting 24–48 hours ahead instead of reacting in real time. The hardware story — non-contact sensing, proportional actuation, human override — is otherwise identical to what's proposed for the real Prayagraj pilot."*
