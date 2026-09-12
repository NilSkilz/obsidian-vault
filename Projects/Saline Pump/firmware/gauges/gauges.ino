// Saline Pump v1 — Stage 7: physical knobs + wet flow calibration.
//
// New in Stage 7 (2026-09-12):
//   - The two KY-040 rotary encoders are LIVE. Turning a knob nudges that
//     side's speed by 1% per detent (clamped to the same 60..100 range as
//     the slider), applied instantly if the pump is already running. The
//     knob and the phone slider edit the SAME variable, so they can never
//     disagree: /status feeds the slider back every 700ms.
//   - Encoder push button: a SHORT press STOPS that side (always, from any
//     state — it is the panic button and it is never ambiguous). A DELIBERATE
//     HOLD of 1.2s STARTS that side. Long-hold-to-start so a brush against
//     the knob can never set a pump running.
//   - Quadrature is decoded in an interrupt, not polled. The draw loop takes
//     ~40ms a frame pushing a 240x240 buffer over SPI, so polling would drop
//     detents on any brisk turn.
//   - FLOW CALIBRATION IS NOW A BUTTON, not a reflash. Hit Calibrate on a
//     side: it runs that pump at 100% for exactly 60s into a measuring jug,
//     counting down on the glass. Type the ml you caught, hit Save, and the
//     ml/min-at-100% constant is stored in NVS and used from then on. It
//     survives reboots and OTA. Every volume on the rig scales off it.
//
// Carried over from Stage 6b:
//
// The GC9A01 faces are unchanged in spirit from Stage 6 (liquid fill with a
// moving two-sine surface, dose ring, big number, state pill). New in 6b:
//
//   - The PHONE PAGE now renders the SAME gauges (the gauge-mockup.html
//     canvas code, live-fed from /status) instead of a plain text readout.
//   - Control is now SPEED, not ml/min. Rob's pumps stall out around 55%
//     duty, which put almost the whole old 1..50 ml/min slider below the
//     stall floor. The speed slider spans 60..100%, so its bottom end
//     ("0") is 60% duty and the whole travel is usable range (2026-09-11).
//   - The big number on both the glass and the phone gauge is duty %, the
//     honest quantity until the wet calibration lands. Delivered/target ml
//     and the reservoir level still come from the flow model (estimates).
//
// Dosing survives: set speed + target ml, hit Start, it stops itself at the
// target. Prime (100%, 10s cap, doesn't count toward the dose), Refill,
// Reset run, low-reservoir auto-stop, 90 min timeout: all as Stage 6.
//
// ── CALIBRATION, DO THIS BEFORE ANY REAL RUN ─────────────────────────────
// mlPerMin100 is the pump's flow at 100% duty. It defaults to a guess
// (~100 ml/min for a 500-series head at 12V) and is WRONG until measured.
// Wet test, now entirely on the phone page: prime the line, put the outlet
// in a measuring jug, hit Calibrate, wait out the 60s countdown, type the
// ml you caught, hit Save. Stored in NVS, survives reboot. Do it per side
// if the two heads differ; the rig keeps one shared figure, so use the
// average of the two or calibrate the side you care most about.
// ─────────────────────────────────────────────────────────────────────────
//
// Safety carried over:
//   - gates forced LOW as the first lines of setup() (GPIO14 boot-twitch).
//   - stall floors from Stage 5 persist (NVS) as a backstop below the UI's
//     own 60% minimum: a requested duty under the floor is clamped UP.
//   - kick-start (250ms at 100%) retained; the kick's extra ml is counted.
//   - firmware hard caps: MAX_TARGET, MAX_RUN_MS, independent of the UI.
//   - low-reservoir auto-stop so a primed line never pumps air.
//   - OTA forces pumps off. E-stop unchanged.
//
// Libraries: Adafruit GC9A01A (+ GFX, BusIO), same as Stage 5.
// Board: ESP32 DevKitC 30-pin, PCB v1 locked pin map (2026-08-20):
//   GPIO14 = Pump L gate   GPIO13 = Pump R gate   GPIO2 = onboard LED
//   Displays (shared SPI): MOSI=23 SCK=18 DC=19 RST=15, CS L=5 / R=4
// Encoders: Enc L CLK/DT/SW = 27/26/25, Enc R CLK/DT/SW = 34/35/32.
// 34/35 are input-only (no internal pull-up) — the KY-040's own 10k
// pull-ups cover CLK/DT, which is exactly why SW sits on 32.

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoOTA.h>
#include <Preferences.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_GC9A01A.h>
#include <Fonts/FreeSansBold24pt7b.h>
#include <Fonts/FreeSansBold9pt7b.h>
#include <Fonts/FreeSans9pt7b.h>
#include <soc/gpio_reg.h>  // REG_READ of the raw input registers, IRAM-safe

// ---- pins (PCB v1, locked) ----
const int PUMP_L_GATE = 14;
const int PUMP_R_GATE = 13;
const int LED = 2;
const int TFT_MOSI = 23;
const int TFT_SCK = 18;
const int TFT_DC = 19;
const int TFT_RST = 15;
const int TFT_CS_L = 5;
const int TFT_CS_R = 4;
// KY-040 encoders. 34/35 are input-only, so Enc R's switch must be on 32.
const int ENC_L_A = 27, ENC_L_B = 26, ENC_L_SW = 25;
const int ENC_R_A = 34, ENC_R_B = 35, ENC_R_SW = 32;

// ---- flow model ----
float mlPerMin100 = 100.0;      // CALIBRATE WET (see header). NVS key "mlmin"
const float CAL_MIN = 5.0;      // sanity bounds on a typed calibration
const float CAL_MAX = 400.0;
const float MAX_TARGET = 600.0;         // ml per run, firmware cap
const float RES_CAPACITY = 1000.0;      // ml, one saline bag/bottle per side
const float RES_LOW_STOP = 30.0;        // stop before the line sucks air
const unsigned long MAX_RUN_MS = 90UL * 60UL * 1000UL;
const unsigned long PRIME_MAX_MS = 10000;
const unsigned long CAL_MS = 60000;  // the calibration run is exactly 60s

// ---- speed range (pumps stall ~55%, so the UI floor is 60) ----
const int UI_MIN_DUTY = 60;
const int KNOB_STEP = 1;                    // % duty per encoder detent
const unsigned long HOLD_START_MS = 1200;   // press-and-hold to start a side

// ---- PWM / kick (from Stage 5 bench findings) ----
const int PWM_FREQ = 1000;
const int PWM_RES = 8;
const int KICK_PCT_MAX = 90;
const unsigned long KICK_MS = 250;

// ---- colours (RGB565 versions of the mockup palette) ----
#define C565(r, g, b) (uint16_t)((((r) & 0xF8) << 8) | (((g) & 0xFC) << 3) | ((b) >> 3))
const uint16_t COL_SLATE = C565(0x14, 0x1b, 0x23);
const uint16_t COL_DEEP = C565(0x0a, 0x3f, 0x74);
const uint16_t COL_MID = C565(0x11, 0x6b, 0xb0);
const uint16_t COL_SURF = C565(0x33, 0xa6, 0xf0);
const uint16_t COL_FOAM = C565(0xa9, 0xe2, 0xff);
const uint16_t COL_RING = C565(0x26, 0x32, 0x3f);
const uint16_t COL_RUN = C565(0x38, 0xd3, 0x9f);
const uint16_t COL_STOP = C565(0xff, 0x5a, 0x5a);
const uint16_t COL_LOW = C565(0xff, 0xb8, 0x4d);
const uint16_t COL_INK = C565(0xff, 0xff, 0xff);
const uint16_t COL_DIM = C565(0xb0, 0xbe, 0xc8);
const uint16_t COL_L_BADGE = C565(0x00, 0xff, 0xff);
const uint16_t COL_R_BADGE = C565(0xff, 0xa5, 0x20);

Adafruit_GC9A01A tftL(TFT_CS_L, TFT_DC, TFT_RST);  // RST on L resets both
Adafruit_GC9A01A tftR(TFT_CS_R, TFT_DC, -1);
// One shared 240x240 frame buffer (112KB). Global so it's allocated at boot
// before WiFi fragments the heap; draw a face into it, push, reuse.
GFXcanvas16 canvas(240, 240);

WebServer server(80);
Preferences prefs;

const char *WIFI_SSID = "PidgeonsNest";
const char *WIFI_PASS = "3b5794e3e9";
bool apFallback = false;           // true while stuck on the fallback AP
unsigned long lastStaRetry = 0;

struct Side {
  bool running = false;
  bool priming = false;
  bool done = false;     // reached target
  bool lowStop = false;  // reservoir guard tripped
  int dutyReq = 70;      // requested speed, % duty (UI sends 60..100)
  float target = 120.0;  // ml
  float delivered = 0;   // ml, this run
  float remain = RES_CAPACITY;
  float elapsedS = 0;
  int minPct = 0;              // stall floor from Stage 5 (NVS), backstop
  int actualDuty = 0;          // what LEDC is holding right now
  unsigned long kickUntil = 0;
  int kickTarget = 0;
  unsigned long primeUntil = 0;
  unsigned long runStartMs = 0;
  bool calibrating = false;      // 60s wide-open run into a jug
  unsigned long calUntil = 0;
};
Side sides[2];  // 0 = L, 1 = R

void pumpWrite(int s, int pct) {
  int pin = (s == 0) ? PUMP_L_GATE : PUMP_R_GATE;
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin, (255 * pct) / 100);
#else
  ledcWrite(s, (255 * pct) / 100);
#endif
  sides[s].actualDuty = pct;
}

// The duty a side will actually run at: the request, clamped up to the
// stall floor (NVS backstop) and into the UI range.
int dutyFor(int s) {
  int duty = constrain(sides[s].dutyReq, UI_MIN_DUTY, 100);
  if (duty < sides[s].minPct) duty = sides[s].minPct;
  return duty;
}

// Push the current requested duty at a side that is already turning. Used
// by both the phone slider and the encoder knob, so they can't diverge.
void applyDuty(int s) {
  Side &S = sides[s];
  if (!S.running) return;
  int duty = dutyFor(s);
  if (S.kickUntil) S.kickTarget = duty;  // still kicking, land on the new one
  else pumpWrite(s, duty);
}

void startRun(int s) {
  Side &S = sides[s];
  if (S.priming || S.calibrating) return;  // one job at a time per side
  if (S.done || S.delivered >= S.target) {  // starting fresh: new run
    S.delivered = 0;
    S.elapsedS = 0;
    S.done = false;
  }
  S.lowStop = false;
  if (S.remain <= RES_LOW_STOP) {  // don't start into an empty bag
    S.lowStop = true;
    return;
  }
  int duty = dutyFor(s);
  S.running = true;
  S.runStartMs = millis();
  if (duty < KICK_PCT_MAX) {
    pumpWrite(s, 100);
    S.kickUntil = millis() + KICK_MS;
    S.kickTarget = duty;
  } else {
    pumpWrite(s, duty);
  }
  Serial.printf("Run %c: duty %d%%, target %.0f ml\n", s == 0 ? 'L' : 'R',
                duty, S.target);
}

void stopRun(int s) {
  Side &S = sides[s];
  S.running = false;
  S.priming = false;
  S.calibrating = false;
  S.kickUntil = 0;
  S.primeUntil = 0;
  S.calUntil = 0;
  pumpWrite(s, 0);
}

void stopAll() {
  stopRun(0);
  stopRun(1);
}

// ---------------------------------------------------------------- encoders
// Table-driven quadrature, decoded in an interrupt. The draw loop spends
// ~40ms a frame shovelling a 240x240 buffer down SPI, so anything polled at
// loop rate drops detents the moment the knob is turned with any pace.
//
// Pin reads go straight at the GPIO input registers rather than through
// digitalRead(): register reads are safe to do from IRAM, a call into a
// flash-resident core function is not.

const int8_t QTAB[16] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};

struct Enc {
  uint8_t pinA, pinB, pinSW;
  volatile uint8_t prev;      // last AB state, 2 bits
  volatile int8_t quarters;   // quarter-steps banked toward a detent
  volatile int16_t detents;   // signed clicks waiting for loop() to spend
  bool swDown;                // debounced switch state
  bool holdFired;             // the 1.2s hold already started this side
  unsigned long swSince;
};
Enc encs[2] = {{ENC_L_A, ENC_L_B, ENC_L_SW, 0, 0, 0, false, false, 0},
               {ENC_R_A, ENC_R_B, ENC_R_SW, 0, 0, 0, false, false, 0}};

static inline int IRAM_ATTR pinLevel(uint8_t pin) {
  return (pin < 32) ? ((REG_READ(GPIO_IN_REG) >> pin) & 1)
                    : ((REG_READ(GPIO_IN1_REG) >> (pin - 32)) & 1);
}

void IRAM_ATTR encISR(void *arg) {
  Enc *e = (Enc *)arg;
  uint8_t now = (uint8_t)((pinLevel(e->pinA) << 1) | pinLevel(e->pinB));
  int8_t d = QTAB[(e->prev << 2) | now];
  e->prev = now;
  if (!d) return;  // bounce or missed edge, ignore rather than guess
  e->quarters += d;
  if (e->quarters >= 4) {        // KY-040 detent = one full quadrature cycle
    e->detents++;
    e->quarters = 0;
  } else if (e->quarters <= -4) {
    e->detents--;
    e->quarters = 0;
  }
}

void encBegin() {
  pinMode(ENC_L_A, INPUT_PULLUP);
  pinMode(ENC_L_B, INPUT_PULLUP);
  pinMode(ENC_L_SW, INPUT_PULLUP);
  pinMode(ENC_R_A, INPUT);  // 34/35 are input-only: no internal pull-up,
  pinMode(ENC_R_B, INPUT);  // the KY-040 module's own 10k resistors do it
  pinMode(ENC_R_SW, INPUT_PULLUP);
  for (int i = 0; i < 2; i++) {
    Enc &e = encs[i];
    e.prev = (uint8_t)((digitalRead(e.pinA) << 1) | digitalRead(e.pinB));
    attachInterruptArg(digitalPinToInterrupt(e.pinA), encISR, &e, CHANGE);
    attachInterruptArg(digitalPinToInterrupt(e.pinB), encISR, &e, CHANGE);
  }
}

// Spend whatever the ISR banked, and service the push switch.
void encService(int s, unsigned long now) {
  Enc &e = encs[s];
  Side &S = sides[s];

  noInterrupts();
  int16_t clicks = e.detents;
  e.detents = 0;
  interrupts();
  if (clicks) {
    S.dutyReq = constrain(S.dutyReq + clicks * KNOB_STEP, UI_MIN_DUTY, 100);
    applyDuty(s);  // no-op unless it's already turning
  }

  bool down = (digitalRead(e.pinSW) == LOW);  // KY-040 SW is active low
  if (down != e.swDown) {
    if (now - e.swSince < 30) return;  // contact bounce
    e.swSince = now;
    e.swDown = down;
    if (down) {
      e.holdFired = false;
    } else if (!e.holdFired) {
      stopRun(s);  // short press = stop, from any state, no questions
      Serial.printf("Knob %c: stop\n", s == 0 ? 'L' : 'R');
    }
  } else if (down && !e.holdFired && now - e.swSince >= HOLD_START_MS) {
    e.holdFired = true;  // deliberate hold = start, a knock never will
    startRun(s);
    Serial.printf("Knob %c: hold-start\n", s == 0 ? 'L' : 'R');
  }
}

// ---------------------------------------------------------------- display

// Centred text at (cx, cy = centre of the glyph box) in the current font.
void drawCentred(const char *txt, int cx, int cy, const GFXfont *font,
                 uint16_t colour) {
  int16_t x1, y1;
  uint16_t w, h;
  canvas.setFont(font);
  canvas.setTextColor(colour);
  canvas.getTextBounds(txt, 0, 0, &x1, &y1, &w, &h);
  canvas.setCursor(cx - w / 2 - x1, cy - h / 2 - y1);
  canvas.print(txt);
}

// Thick arc: filled discs marched along the radius. a0/a1 in radians,
// 12 o'clock = -PI/2, clockwise positive.
void arcRing(int cx, int cy, int r, int half, float a0, float a1,
             uint16_t colour) {
  float step = 1.5f / r;  // ~1.5px of travel per disc, no gaps
  for (float a = a0; a <= a1; a += step)
    canvas.fillCircle(cx + (int)(r * cosf(a)), cy + (int)(r * sinf(a)), half,
                      colour);
}

float wavePhase = 0;

void drawFace(int s) {
  Side &S = sides[s];
  const int W = 240, H = 240, cx = 120, cy = 120;

  canvas.fillScreen(COL_SLATE);

  // liquid: per-column waterline from two summed sines, calm when stopped
  float level = S.remain / RES_CAPACITY;
  level = constrain(level, 0.0f, 1.0f);
  float act = (S.running || S.priming) ? 1.0f : 0.35f;
  float baseY = H - level * H;
  const float TAU = 6.2831853f;
  for (int x = 0; x < W; x++) {
    float w = 5.5f * act * sinf((x / 240.0f * TAU) * 1.6f + wavePhase * 1.8f)
            + 3.0f * act * sinf((x / 240.0f * TAU) * 2.7f - wavePhase * 2.6f + 1.3f);
    int y = (int)(baseY + w);
    if (level >= 0.995f) y = 0;
    if (y < 0) y = 0;
    if (y >= H) continue;
    // fake the mockup's gradient with three bands: surface, mid, deep
    int surfEnd = min(y + 6, H);
    int midEnd = min(y + 34, H);
    canvas.drawFastVLine(x, y, surfEnd - y, COL_SURF);
    if (midEnd > surfEnd) canvas.drawFastVLine(x, surfEnd, midEnd - surfEnd, COL_MID);
    if (H > midEnd) canvas.drawFastVLine(x, midEnd, H - midEnd, COL_DEEP);
    if (level > 0.02f && level < 0.99f)
      canvas.drawFastVLine(x, y, 2, COL_FOAM);  // foam highlight
  }

  // dose-progress ring around the rim
  float frac = (S.target > 0) ? S.delivered / S.target : 0;
  frac = constrain(frac, 0.0f, 1.0f);
  const float top = -1.5707963f;
  arcRing(cx, cy, 111, 3, 0, TAU, COL_RING);
  uint16_t ringCol = (S.running || S.done) ? COL_RUN : COL_STOP;
  if (frac > 0.002f) arcRing(cx, cy, 111, 3, top, top + frac * TAU, ringCol);

  // side badge (top)
  drawCentred(s == 0 ? "LEFT" : "RIGHT", cx, 38, &FreeSansBold9pt7b,
              s == 0 ? COL_L_BADGE : COL_R_BADGE);

  // state pill
  const char *pill = S.calibrating ? "CAL"
                   : S.priming     ? "PRIME"
                   : S.running     ? "RUN"
                   : S.lowStop     ? "LOW"
                   : S.done        ? "DONE"
                                   : "STOP";
  uint16_t pillCol = (S.calibrating || S.priming || S.lowStop) ? COL_LOW
                   : (S.running || S.done)                     ? COL_RUN
                                                               : COL_STOP;
  int16_t x1, y1;
  uint16_t tw, th;
  canvas.setFont(&FreeSansBold9pt7b);
  canvas.getTextBounds(pill, 0, 0, &x1, &y1, &tw, &th);
  canvas.fillRoundRect(cx - tw / 2 - 9, 52, tw + 18, 22, 11, pillCol);
  drawCentred(pill, cx, 63, &FreeSansBold9pt7b, C565(0x08, 0x11, 0x0d));

  // big number: the duty actually on the gate (or what Start would give)
  int shown = (S.running || S.priming || S.calibrating) ? S.actualDuty
                                                        : dutyFor(s);
  char buf[16];
  snprintf(buf, sizeof buf, "%d", shown);
  drawCentred(buf, cx, cy + 2, &FreeSansBold24pt7b, COL_INK);
  drawCentred("speed %", cx, cy + 34, &FreeSans9pt7b, COL_DIM);

  // bottom line: the dose normally, the calibration countdown during a cal
  if (S.calibrating) {
    long left = (long)(S.calUntil - millis());
    if (left < 0) left = 0;
    snprintf(buf, sizeof buf, "CATCH IT: %lds", (left + 999) / 1000);
    drawCentred(buf, cx, cy + 62, &FreeSansBold9pt7b, COL_LOW);
    drawCentred("into the jug", cx, cy + 84, &FreeSans9pt7b, COL_DIM);
  } else {
    snprintf(buf, sizeof buf, "%.0f / %.0f ml", S.delivered, S.target);
    drawCentred(buf, cx, cy + 62, &FreeSansBold9pt7b, COL_INK);
    int m = (int)(S.elapsedS / 60), sec = (int)S.elapsedS % 60;
    snprintf(buf, sizeof buf, "%02d:%02d", m, sec);
    drawCentred(buf, cx, cy + 84, &FreeSans9pt7b, COL_DIM);
  }

  Adafruit_GC9A01A &tft = (s == 0) ? tftL : tftR;
  tft.drawRGBBitmap(0, 0, canvas.getBuffer(), 240, 240);
}

// ---------------------------------------------------------------- web UI
// The gauge-mockup.html canvas gauges, live-fed from /status. Slider spans
// 60..100% duty: bottom of travel = 60%, everything on it is usable range.

const char PAGE[] PROGMEM = R"HTML(<!doctype html><html><head>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Saline Pump</title><style>
:root{--bg:#0c0f14;--panel:#141a22;--ink:#e7edf3;--muted:#8aa0b3}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
 padding:14px 12px 90px;text-align:center}
h1{font-size:17px;font-weight:650;color:var(--muted);margin:2px 0 14px}
.gauges{display:flex;gap:22px;justify-content:center;flex-wrap:wrap}
.unit{background:var(--panel);border:1px solid #202a35;border-radius:16px;
 padding:16px 14px 12px;width:290px;max-width:100%}
.glass{width:240px;height:240px;border-radius:50%;margin:0 auto;
 box-shadow:0 0 0 6px #05070a,0 0 0 8px #262f3a,0 10px 26px rgba(0,0,0,.55);
 overflow:hidden;background:#12181f}
canvas{display:block;width:240px;height:240px}
.row{display:grid;grid-template-columns:52px 1fr 56px;gap:10px;align-items:center;
 margin:12px 0 4px;font-size:13px}
.row label{text-align:left;color:var(--muted)}
.row output{text-align:right;font-variant-numeric:tabular-nums}
input[type=range]{width:100%;height:34px;accent-color:#33a6f0}
input[type=number]{width:64px;font-size:15px;background:#1d2732;color:var(--ink);
 border:1px solid #2c3948;border-radius:8px;padding:6px;text-align:right}
.btns{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin-top:8px}
button{background:#1d2732;color:var(--ink);border:1px solid #2c3948;
 border-radius:10px;padding:10px 12px;font-size:13px}
button.go{background:#1d5c46;border-color:#2a8666}
button.warn{background:#5c4a1d;border-color:#866f2a}
.stopall{position:fixed;left:12px;right:12px;bottom:12px;background:#a00;
 border:0;color:#fff;font-size:19px;font-weight:700;padding:16px;border-radius:14px;
 box-shadow:0 6px 18px rgba(0,0,0,.5)}
small{display:block;color:#667;margin-top:14px;line-height:1.5}
.cal{background:var(--panel);border:1px solid #202a35;border-radius:16px;
 padding:14px;margin:18px auto 0;max-width:602px}
.cal h2{font-size:13px;font-weight:650;color:var(--muted);margin:0 0 10px;
 letter-spacing:.04em}
.calrow{display:flex;gap:8px;justify-content:center;align-items:center;
 flex-wrap:wrap;margin-bottom:8px;font-size:13px}
.calnow{color:var(--muted);font-size:12px;margin-top:6px}
.calnow b{color:var(--ink);font-variant-numeric:tabular-nums}
</style></head><body>
<h1>SALINE PUMP</h1>
<div class=gauges id=g></div>
<div class=cal><h2>FLOW CALIBRATION</h2>
<div class=calrow>
<button class=warn onclick="fetch('/cal?side=L')">Run L 60s</button>
<button class=warn onclick="fetch('/cal?side=R')">Run R 60s</button>
</div>
<div class=calrow>
<label>Caught</label>
<input type=number id=cm min=5 max=400 step=.1 placeholder=ml>
<span>ml in 60s</span>
<button class=go onclick=saveCal()>Save</button>
</div>
<div class=calnow id=cnow>using <b>?</b> ml/min at 100%</div></div>
<small>Slider bottom = 60% power (pumps stall below ~55%). Volumes are
estimates until the flow calibration above is done. Prime auto-stops after
10s. Knobs: turn = speed, short press = stop that side, hold 1.2s = start.
E-stop kills pumps regardless of anything on this page.</small>
<button class=stopall onclick="fetch('/stop')">STOP ALL</button>
<script>
const TAU=Math.PI*2,SIDES=['L','R'];
const C={slateTop:'#141b23',slateBot:'#0e141b',deep:'#0a3f74',mid:'#116bb0',
 surf:'#33a6f0',foam:'#a9e2ff',ring:'#26323f',run:'#38d39f',stop:'#ff5a5a',
 warn:'#ffb84d',ink:'#fff',dim:'rgba(255,255,255,.72)',
 badgeL:'#0ff',badgeR:'#ffa520'};
let editing={};
function card(s){return `<div class=unit>
<div class=glass><canvas id=c${s} width=240 height=240></canvas></div>
<div class=row><label>Speed</label>
<input type=range min=60 max=100 step=1 value=70 id=s${s}
 onpointerdown="editing['s${s}']=1"
 oninput="o${s}.textContent=this.value+'%'"
 onpointerup="editing['s${s}']=0;send('${s}')"
 onchange="editing['s${s}']=0;send('${s}')"><output id=o${s}>70%</output></div>
<div class=row><label>Target</label>
<input type=number min=10 max=600 step=10 value=120 id=t${s}
 onfocus="editing['t${s}']=1" onblur="editing['t${s}']=0"
 onchange="send('${s}')"
 style=justify-self:start><output>ml</output></div>
<div class=btns>
<button class=go onclick="fetch('/run?side=${s}&on=1')">Start</button>
<button onclick="fetch('/run?side=${s}&on=0')">Stop</button>
<button class=warn onclick="fetch('/prime?side=${s}')">Prime</button>
<button onclick="fetch('/reset?side=${s}')">Reset</button>
<button onclick="fetch('/refill?side=${s}')">Refilled</button>
</div></div>`}
g.innerHTML=card('L')+card('R');
function roundRect(x,y,w,h,r,ctx){ctx.beginPath();ctx.moveTo(x+r,y);
 ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);
 ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath()}
function fmtT(s){const m=Math.floor(s/60),ss=Math.floor(s%60);
 return String(m).padStart(2,'0')+':'+String(ss).padStart(2,'0')}
function gauge(side){
 const ctx=document.getElementById('c'+side).getContext('2d');
 const st={lvl:1,duty:70,run:0,prime:0,done:0,low:0,cal:0,calleft:0,
  del:0,tgt:120,el:0};
 let t=0;
 function draw(){
  const W=240,H=240,cx=120,cy=120,R=120;
  ctx.clearRect(0,0,W,H);
  ctx.save();ctx.beginPath();ctx.arc(cx,cy,R,0,TAU);ctx.clip();
  let bg=ctx.createLinearGradient(0,0,0,H);
  bg.addColorStop(0,C.slateTop);bg.addColorStop(1,C.slateBot);
  ctx.fillStyle=bg;ctx.fillRect(0,0,W,H);
  const lvl=Math.max(0,Math.min(1,st.lvl)),baseY=H-lvl*H;
  const act=(st.run||st.prime)?1:.35,a1=5.5,a2=3;
  let lg=ctx.createLinearGradient(0,baseY-14,0,H);
  lg.addColorStop(0,C.surf);lg.addColorStop(.28,C.mid);lg.addColorStop(1,C.deep);
  ctx.beginPath();ctx.moveTo(0,H);
  for(let x=0;x<=W;x+=2){
   const w=a1*act*Math.sin((x/W*TAU)*1.6+t*1.8)
        +a2*act*Math.sin((x/W*TAU)*2.7-t*2.6+1.3);
   ctx.lineTo(x,baseY+w)}
  ctx.lineTo(W,H);ctx.closePath();ctx.fillStyle=lg;ctx.fill();
  if(lvl>.02&&lvl<.99){ctx.beginPath();
   for(let x=0;x<=W;x+=2){
    const w=a1*act*Math.sin((x/W*TAU)*1.6+t*1.8)
         +a2*act*Math.sin((x/W*TAU)*2.7-t*2.6+1.3);
    x===0?ctx.moveTo(x,baseY+w):ctx.lineTo(x,baseY+w)}
   ctx.strokeStyle=C.foam;ctx.globalAlpha=.55;ctx.lineWidth=2;ctx.stroke();
   ctx.globalAlpha=1}
  ctx.restore();
  const rr=R-9,frac=Math.max(0,Math.min(1,st.tgt>0?st.del/st.tgt:0));
  ctx.lineWidth=7;ctx.lineCap='round';
  ctx.strokeStyle=C.ring;ctx.beginPath();ctx.arc(cx,cy,rr,0,TAU);ctx.stroke();
  if(frac>.002){ctx.strokeStyle=(st.run||st.done)?C.run:C.stop;
   ctx.beginPath();ctx.arc(cx,cy,rr,-Math.PI/2,-Math.PI/2+frac*TAU);ctx.stroke()}
  ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.shadowColor='rgba(0,0,0,.55)';ctx.shadowBlur=6;
  ctx.font='700 14px -apple-system,Segoe UI,Roboto,sans-serif';
  ctx.fillStyle=side==='L'?C.badgeL:C.badgeR;
  ctx.fillText(side==='L'?'LEFT':'RIGHT',cx,40);
  const pill=st.cal?'CAL':st.prime?'PRIME':st.run?'RUN':st.low?'LOW'
   :st.done?'DONE':'STOP';
  const pcol=(st.cal||st.prime||st.low)?C.warn:(st.run||st.done)?C.run:C.stop;
  ctx.font='700 12px -apple-system,Segoe UI,Roboto,sans-serif';
  const pw=ctx.measureText(pill).width+18;
  ctx.shadowBlur=0;ctx.fillStyle=pcol;
  roundRect(cx-pw/2,52,pw,20,10,ctx);ctx.fill();
  ctx.fillStyle='#08110d';ctx.fillText(pill,cx,62.5);
  ctx.shadowColor='rgba(0,0,0,.55)';ctx.shadowBlur=6;
  ctx.fillStyle=C.ink;
  ctx.font='800 52px -apple-system,Segoe UI,Roboto,sans-serif';
  ctx.fillText(String(Math.round(st.duty)),cx,cy+2);
  ctx.font='600 15px -apple-system,Segoe UI,Roboto,sans-serif';
  ctx.fillStyle=C.dim;ctx.fillText('speed %',cx,cy+34);
  ctx.font='700 16px -apple-system,Segoe UI,Roboto,sans-serif';
  if(st.cal){ctx.fillStyle=C.warn;
   ctx.fillText('CATCH IT: '+st.calleft+'s',cx,cy+64);
   ctx.font='600 13px -apple-system,Segoe UI,Roboto,sans-serif';
   ctx.fillStyle=C.dim;ctx.fillText('into the jug',cx,cy+84)}
  else{ctx.fillStyle=C.ink;
   ctx.fillText(Math.round(st.del)+' / '+Math.round(st.tgt)+' ml',cx,cy+64);
   ctx.font='600 13px -apple-system,Segoe UI,Roboto,sans-serif';
   ctx.fillStyle=C.dim;ctx.fillText(fmtT(st.el),cx,cy+84)}
  ctx.shadowBlur=0}
 return {st,tick:dt=>{t+=dt;draw()}}}
const G={L:gauge('L'),R:gauge('R')};
async function saveCal(){const v=document.getElementById('cm').value;
 const r=await fetch('/calsave?ml='+v);
 document.getElementById('cnow').style.color=r.ok?'#38d39f':'#ff5a5a';
 if(r.ok)document.getElementById('cm').value='';poll()}
function send(s){fetch('/set?side='+s
 +'&duty='+document.getElementById('s'+s).value
 +'&target='+document.getElementById('t'+s).value)}
async function poll(){try{
 const j=await(await fetch('/status')).json();
 for(const s of SIDES){const d=j[s],g=G[s].st;
  g.lvl=d.lvl;g.run=d.run;g.prime=d.prime;g.done=d.done;g.low=d.low;
  g.cal=d.cal;g.calleft=d.calleft;
  g.del=d.del;g.tgt=d.tgt;g.el=d.el;
  g.duty=(d.run||d.prime||d.cal)?d.duty:d.req;
  if(!editing['s'+s]){const sl=document.getElementById('s'+s);
   sl.value=d.req;document.getElementById('o'+s).textContent=d.req+'%'}
  if(!editing['t'+s])document.getElementById('t'+s).value=d.tgt}
 document.getElementById('cnow').innerHTML=
  'using <b>'+j.mlmin.toFixed(1)+'</b> ml/min at 100%';
}catch(e){}}
setInterval(poll,700);poll();
let last=performance.now();
(function loop(){const now=performance.now();
 const dt=Math.min(.05,(now-last)/1000);last=now;
 G.L.tick(dt);G.R.tick(dt);requestAnimationFrame(loop)})();
</script></body></html>)HTML";

int sideArg() { return (server.arg("side") == "R") ? 1 : 0; }

// Whole seconds left on a calibration run, 0 when there isn't one.
long calLeft(int s) {
  if (!sides[s].calibrating) return 0;
  long ms = (long)(sides[s].calUntil - millis());
  return ms > 0 ? (ms + 999) / 1000 : 0;
}

void handleSet() {
  int s = sideArg();
  Side &S = sides[s];
  if (server.hasArg("duty"))
    S.dutyReq = constrain(server.arg("duty").toInt(), UI_MIN_DUTY, 100);
  if (server.hasArg("target"))
    S.target = constrain(server.arg("target").toFloat(), 10.0f, MAX_TARGET);
  applyDuty(s);  // live speed change if it's already turning
  server.send(200, "text/plain", "ok");
}

void handleRun() {
  int s = sideArg();
  if (server.arg("on") == "1") startRun(s);
  else stopRun(s);
  server.send(200, "text/plain", "ok");
}

void handlePrime() {
  int s = sideArg();
  Side &S = sides[s];
  if (S.running || S.calibrating) {
    server.send(409, "text/plain", "stop the run first");
    return;
  }
  if (S.priming) {  // second tap = stop priming
    stopRun(s);
  } else if (S.remain > RES_LOW_STOP) {
    S.priming = true;
    S.lowStop = false;
    S.primeUntil = millis() + PRIME_MAX_MS;
    pumpWrite(s, 100);
  }
  server.send(200, "text/plain", "ok");
}

void handleReset() {
  int s = sideArg();
  stopRun(s);
  sides[s].delivered = 0;
  sides[s].elapsedS = 0;
  sides[s].done = false;
  sides[s].lowStop = false;
  server.send(200, "text/plain", "ok");
}

void handleRefill() {
  int s = sideArg();
  sides[s].remain = RES_CAPACITY;
  sides[s].lowStop = false;
  server.send(200, "text/plain", "ok");
}

// Start the 60s wide-open run into a measuring jug. Refuses if that side
// is doing anything else, so a cal can never be layered over a real dose.
void handleCal() {
  int s = sideArg();
  Side &S = sides[s];
  if (S.calibrating) {  // second tap = abandon it
    stopRun(s);
    server.send(200, "text/plain", "cancelled");
    return;
  }
  if (S.running || S.priming) {
    server.send(409, "text/plain", "stop the run first");
    return;
  }
  S.calibrating = true;
  S.lowStop = false;
  S.calUntil = millis() + CAL_MS;
  pumpWrite(s, 100);
  Serial.printf("Calibration run %c: 60s at 100%%\n", s == 0 ? 'L' : 'R');
  server.send(200, "text/plain", "ok");
}

// The measured ml caught in 60s IS the ml/min figure. Persisted to NVS so
// it survives a reboot or an OTA push.
void handleCalSave() {
  float ml = server.arg("ml").toFloat();
  if (ml < CAL_MIN || ml > CAL_MAX) {
    server.send(400, "text/plain", "out of range");
    return;
  }
  mlPerMin100 = ml;
  prefs.putFloat("mlmin", mlPerMin100);
  Serial.printf("Calibrated: %.1f ml/min at 100%%\n", mlPerMin100);
  server.send(200, "text/plain", "ok");
}

void handleStatus() {
  char buf[600];
  int n = snprintf(buf, sizeof buf, "{\"mlmin\":%.1f,", mlPerMin100);
  for (int s = 0; s < 2; s++) {
    Side &S = sides[s];
    n += snprintf(buf + n, sizeof buf - n,
                  "\"%c\":{\"run\":%d,\"prime\":%d,\"done\":%d,\"low\":%d,"
                  "\"cal\":%d,\"calleft\":%ld,"
                  "\"req\":%d,\"duty\":%d,\"tgt\":%.0f,\"del\":%.1f,"
                  "\"el\":%.0f,\"lvl\":%.3f}%s",
                  s == 0 ? 'L' : 'R', S.running, S.priming, S.done, S.lowStop,
                  S.calibrating, calLeft(s),
                  dutyFor(s), S.actualDuty, S.target, S.delivered, S.elapsedS,
                  S.remain / RES_CAPACITY, s == 0 ? "," : "}");
  }
  server.send(200, "application/json", buf);
}

// ---------------------------------------------------------------- setup

void setup() {
  // FIRST lines, before serial, before anything: gates off (GPIO14 twitch).
  pinMode(PUMP_L_GATE, OUTPUT);
  digitalWrite(PUMP_L_GATE, LOW);
  pinMode(PUMP_R_GATE, OUTPUT);
  digitalWrite(PUMP_R_GATE, LOW);

  pinMode(TFT_CS_L, OUTPUT);
  digitalWrite(TFT_CS_L, HIGH);
  pinMode(TFT_CS_R, OUTPUT);
  digitalWrite(TFT_CS_R, HIGH);
  pinMode(LED, OUTPUT);

  Serial.begin(115200);
  delay(300);
  Serial.println("\nSaline Pump Stage 7: knobs + calibration. Pumps start OFF.");
  if (!canvas.getBuffer()) {
    Serial.println("FATAL: frame buffer allocation failed");
    while (true) delay(1000);
  }

#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PUMP_L_GATE, PWM_FREQ, PWM_RES);
  ledcAttach(PUMP_R_GATE, PWM_FREQ, PWM_RES);
#else
  ledcSetup(0, PWM_FREQ, PWM_RES);
  ledcAttachPin(PUMP_L_GATE, 0);
  ledcSetup(1, PWM_FREQ, PWM_RES);
  ledcAttachPin(PUMP_R_GATE, 1);
#endif
  pumpWrite(0, 0);
  pumpWrite(1, 0);

  prefs.begin("pump", false);
  sides[0].minPct = prefs.getInt("minL", 0);  // stall floors from Stage 5
  sides[1].minPct = prefs.getInt("minR", 0);
  mlPerMin100 = prefs.getFloat("mlmin", 100.0f);
  Serial.printf("Stall floors: L=%d%% R=%d%% (UI floor %d%%)\n",
                sides[0].minPct, sides[1].minPct, UI_MIN_DUTY);
  Serial.printf("Flow: %.1f ml/min at 100%%%s\n", mlPerMin100,
                prefs.isKey("mlmin") ? "" : "  <-- UNCALIBRATED, guess");

  encBegin();

  SPI.begin(TFT_SCK, -1, TFT_MOSI, -1);
  tftL.begin(27000000);
  tftR.begin(27000000);
  drawFace(0);
  drawFace(1);

  // WiFi. The old one-shot 15s window then AP-forever stranded the board
  // after an OTA reboot (2026-09-11): first reconnect after a soft reset
  // can miss the window, and there was no way back without a power cycle.
  // Now: AP_STA fallback, and loop() keeps retrying the house WiFi from
  // AP mode; on success the AP is torn down.
  WiFi.persistent(false);
  WiFi.setAutoReconnect(true);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 20000) delay(250);
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi up, IP: ");
    Serial.println(WiFi.localIP());
  } else {
    apFallback = true;
    WiFi.mode(WIFI_AP_STA);
    WiFi.softAP("SalinePump-Test", "primefirst");
    WiFi.begin(WIFI_SSID, WIFI_PASS);  // keeps trying underneath the AP
    Serial.print("Fallback AP up (still retrying STA), AP IP: ");
    Serial.println(WiFi.softAPIP());
  }

  ArduinoOTA.setHostname("salinepump");
  ArduinoOTA.setPassword("primefirst");
  ArduinoOTA.onStart([]() {
    stopAll();
    Serial.println("OTA starting, pumps forced off");
  });
  ArduinoOTA.begin();

  server.on("/", []() { server.send_P(200, "text/html", PAGE); });
  server.on("/set", handleSet);
  server.on("/run", handleRun);
  server.on("/prime", handlePrime);
  server.on("/reset", handleReset);
  server.on("/refill", handleRefill);
  server.on("/stop", []() {
    stopAll();
    server.send(200, "text/plain", "stopped");
  });
  server.on("/cal", handleCal);
  server.on("/calsave", handleCalSave);
  server.on("/status", handleStatus);
  server.begin();
  Serial.println("UI: http://salinepump.local/");
}

// ---------------------------------------------------------------- loop

void loop() {
  unsigned long now = millis();

  // kick-start settle
  for (int s = 0; s < 2; s++) {
    Side &S = sides[s];
    if (S.kickUntil && now >= S.kickUntil) {
      S.kickUntil = 0;
      pumpWrite(s, S.kickTarget);
    }
    if (S.priming && now >= S.primeUntil) stopRun(s);
    if (S.calibrating && (long)(now - S.calUntil) >= 0) {
      stopRun(s);
      Serial.printf("Calibration run %c finished, measure the jug\n",
                    s == 0 ? 'L' : 'R');
    }
    // Guard the bag during a cal too: 60s wide open is ~100ml of it.
    if (S.calibrating && S.remain <= RES_LOW_STOP) {
      stopRun(s);
      S.lowStop = true;
    }
    encService(s, now);
  }

  // flow integration: dt against the duty the gate is REALLY holding
  // (kick bursts and stall-floor clamps included, so the count is honest)
  static unsigned long lastInteg = 0;
  if (lastInteg == 0) lastInteg = now;
  float dtMin = (now - lastInteg) / 60000.0f;
  if (dtMin > 0) {
    lastInteg = now;
    for (int s = 0; s < 2; s++) {
      Side &S = sides[s];
      float flow = mlPerMin100 * S.actualDuty / 100.0f * dtMin;
      if (flow > 0) S.remain = max(0.0f, S.remain - flow);
      if (S.running) {
        S.delivered += flow;
        S.elapsedS += dtMin * 60.0f;
        if (S.delivered >= S.target) {  // dose complete
          stopRun(s);
          S.done = true;
          Serial.printf("Dose done %c: %.0f ml\n", s == 0 ? 'L' : 'R',
                        S.delivered);
        } else if (S.remain <= RES_LOW_STOP) {  // never pump air
          stopRun(s);
          S.lowStop = true;
          Serial.printf("LOW RESERVOIR stop %c\n", s == 0 ? 'L' : 'R');
        } else if (now - S.runStartMs > MAX_RUN_MS) {
          stopRun(s);
          Serial.printf("Max-runtime stop %c\n", s == 0 ? 'L' : 'R');
        }
      }
    }
  }

  // redraw: one face per tick, alternating, so the loop never stalls long
  static unsigned long lastDraw = 0;
  static int drawSide = 0;
  if (now - lastDraw >= 40) {
    lastDraw = now;
    wavePhase += 0.06f;
    drawFace(drawSide);
    drawSide = 1 - drawSide;
  }

  // WiFi self-rescue: while on the fallback AP, keep knocking on the house
  // network every 30s; the moment STA connects, drop the AP and carry on.
  if (apFallback) {
    if (WiFi.status() == WL_CONNECTED) {
      apFallback = false;
      WiFi.softAPdisconnect(true);
      WiFi.mode(WIFI_STA);
      Serial.print("STA recovered, IP: ");
      Serial.println(WiFi.localIP());
    } else if (now - lastStaRetry > 30000) {
      lastStaRetry = now;
      WiFi.begin(WIFI_SSID, WIFI_PASS);
    }
  }

  // LED: solid while any pump runs, short heartbeat blink when idle
  bool anyRun = sides[0].running || sides[1].running || sides[0].priming ||
                sides[1].priming || sides[0].calibrating || sides[1].calibrating;
  digitalWrite(LED, anyRun ? HIGH : ((now % 1000) < 80 ? HIGH : LOW));

  ArduinoOTA.handle();
  server.handleClient();
}
