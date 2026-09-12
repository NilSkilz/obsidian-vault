// Saline Pump v1 - Stage 7d: Tide-themed phone UI, split into Run/Settings.
//
// ── STAGE 7d: THE PAGE STOPS BEING A COCKPIT (2026-09-12) ──────────────
// Rob's verdict on 7c's page: confusing, the big number looked low-res, and
// calibration felt like it took ages to react. All three were real.
//
//   1. TWO VIEWS, not one wall. "Run" is the two gauges, speed, target and
//      Start/Stop/Prime, nothing else. "Settings" holds flow calibration,
//      refill/reset, the knobs and the safety notes. STOP ALL stays pinned
//      to the bottom of both, always one thumb away.
//   2. THE BIG NUMBER IS CRISP NOW. The canvas was 240x240 backing pixels
//      stretched over a 240 CSS px box on a 2-3x phone screen, i.e. every
//      glyph upscaled by the browser. The backing store is now sized to
//      devicePixelRatio (capped at 2) with the context scaled to match, so
//      text is rendered at device resolution.
//   3. RESPONSIVENESS, three separate causes:
//      a. EVERY endpoint now answers with the full status JSON instead of
//         "ok", so a tap gets fresh truth in ONE round trip. Previously the
//         page waited for the next poll to find out what its own command
//         did: up to 700ms of nothing happening.
//      b. ONE REQUEST AT A TIME. WebServer serves a single client, so
//         overlapping fetches sat in the TCP backlog. All traffic goes
//         through a queue on the page, and a button tap jumps the queue.
//         Polling is adaptive: 400ms while anything is running, 1500ms
//         idle, 250ms for 2.5s after a tap.
//      c. THE NUMBERS MOVE BETWEEN POLLS. Delivered ml, elapsed time, the
//         reservoir level and the calibration countdown are advanced
//         locally off the known flow rate and corrected by each poll, so
//         the 60s countdown ticks every second instead of lurching.
//      Also: taps patch the UI optimistically before the request goes out,
//      and the draw loop is 30fps when active / 10fps idle / nothing at all
//      on the Settings tab or a backgrounded page (it was a flat 60fps
//      redraw of two faces forever, which is what made touch feel sticky).
//   4. THEMING lifted from Tide (mission-control/src/tide/tide.css): dark
//      ground, one gradient voice, an ambient breathing glow, hairline
//      sections instead of boxed cards, pill buttons. Tide runs coral/rose;
//      this rig runs TEAL with coral as the rationed accent. The GC9A01
//      faces were recoloured to the same palette so the glass and the phone
//      read as one object.
// ──────────────────────────────────────────────────────────────────────
//
// ── STAGE 7c: BENCH MODE (2026-09-12) ────────────────────────────────────
// The ESP32 is out of the PCB socket and loose on the desk while we work on
// the phone UI. Nothing is plugged into it: no round screens, no KY-040s.
// Two switches near the top of this file (ENABLE_SCREENS / ENABLE_KNOBS)
// now compile those peripherals OUT rather than merely skipping them:
//   * no 112KB frame buffer allocated at all (~112KB more heap for WiFi),
//   * no SPI, no CS pins driven, no per-frame redraw burning ~40ms a tick,
//   * encoder pins never even set to INPUT, so nothing can attach an
//     interrupt to a floating GPIO34/35.
// The phone page shows an amber BENCH MODE banner and hides the KNOBS card
// so it is obvious which build is on the board. Pumps, the firmware caps,
// the stall floor, the low-reservoir stop and the E-stop are all unchanged
// and still live. Board back in the socket -> set both to 1 and reflash.
// ─────────────────────────────────────────────────────────────────────────
//
// ── STAGE 7b: STOP GUESSING, MAKE THE BOARD TALK (2026-09-12) ────────────
// 7a's floating-pin theory did not fix it: still no LED, still apparently
// dead. So 7b stops theorising and instruments the boot instead.
//   * Serial comes up FIRST, before anything that can hang, and prints a
//     build banner (STAGE 7b + compile timestamp). If that banner is not on
//     the serial monitor, the board is NOT running this binary and the
//     problem is the upload, not the code.
//   * esp_reset_reason() and the heap figures are printed at boot, so a
//     panic loop or a failed frame-buffer malloc identifies itself.
//   * Every risky init step prints a numbered checkpoint BEFORE it runs.
//     Whatever the last line on the monitor is, that is where it died.
//   * The boot blink is now 3 x 250ms (1.5s), not 3 x 60ms. The old one was
//     360ms total and genuinely easy to miss.
//   * THE FRAME BUFFER NO LONGER COSTS A BOOT. 7a halted forever in a
//     while(true) if the 112KB canvas malloc failed, which looks exactly
//     like "dead board": no LED, no web server, nothing. Now a failed
//     allocation just disables the two round screens and says so; WiFi and
//     the phone UI still come up. Same principle as the knobs: no single
//     peripheral gets to take the whole rig down.
// ─────────────────────────────────────────────────────────────────────────
//
// ── STAGE 7a BOOT FIX (2026-09-12) ───────────────────────────────────────
// Stage 7 as first written would not boot: no heartbeat LED, no web server,
// a board that looked dead. Cause was in this file, not on the bench.
// setup() armed CHANGE interrupts on all four encoder lines whether or not
// an encoder was plugged in. Enc R's CLK/DT are GPIO34/35, which are
// INPUT-ONLY and have no internal pull-up, so with the KY-040s not yet
// wired (they mount to an enclosure still on the printer) both pins floated
// and chattered. Two floating pins firing edge interrupts flat out starve
// loop(): no LED, no HTTP, nothing. Enc L on 27/26 was innocent, its
// internal pull-ups hold it quiet when unwired.
// Fixed three ways, because a knob must never cost a boot:
//   1. Knobs are OFF until declared wired, per side, on the phone page
//      ("KNOBS" panel). The choice sticks in NVS.
//   2. Before any interrupt is armed, the pair is watched for 40ms; a
//      floating pin flickers and is refused.
//   3. A guard in loop() counts ISR entries per second and disarms any pin
//      firing like a floating input (>4000/s), clearing the opt-in so the
//      next boot is clean.
// Also: QTAB moved to DRAM (an IRAM ISR reading a flash table crashes if it
// fires during an NVS write or an OTA), and setup() now blinks the LED three
// times on entry, so "did it boot at all" is answerable without serial.
// Worth doing in hardware anyway: 10k pull-ups to 3V3 on 34 and 35 make
// those pins safe even with nothing plugged in.
// ─────────────────────────────────────────────────────────────────────────
//
// New in Stage 7 (2026-09-12):
//   - The two KY-040 rotary encoders are supported (armed per side once
//     enabled on the page, see the boot fix above). Turning a knob nudges that
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
#include <esp_system.h>    // esp_reset_reason(), for the boot diagnostics

// ---- BENCH MODE (2026-09-12) ----------------------------------------
// The board is out of the PCB socket and sitting bare on the desk: no
// screens plugged in, no KY-040s, every peripheral pin floating. With
// these at 0 the hardware is compiled OUT, not merely skipped:
//   ENABLE_SCREENS 0 -> no 112KB frame buffer, no SPI, no CS pins, and
//                       loop() stops spending ~40ms a frame on a redraw
//                       nobody can see. Roughly 112KB more heap for WiFi.
//   ENABLE_KNOBS   0 -> encoder pins are never even set to INPUT, so
//                       nothing can attach an interrupt to a floating
//                       GPIO34/35 and starve the loop.
// What is left is exactly the bit we are working on: WiFi, the phone UI,
// and the two pump gates (which still come up OFF and still honour every
// cap, the stall floor, the low-reservoir stop and the E-stop).
// PUT THE BOARD BACK IN THE SOCKET -> set both to 1 and reflash.
#define ENABLE_SCREENS 0
#define ENABLE_KNOBS 0

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
// Teal, matching the phone page's Tide-derived palette so the glass and the
// phone read as the same object. Teal is the voice, coral the accent.
const uint16_t COL_SLATE = C565(0x10, 0x1a, 0x1d);
const uint16_t COL_DEEP = C565(0x07, 0x44, 0x3f);
const uint16_t COL_MID = C565(0x0d, 0x94, 0x88);
const uint16_t COL_SURF = C565(0x2d, 0xd4, 0xbf);
const uint16_t COL_FOAM = C565(0xb6, 0xf5, 0xea);
const uint16_t COL_RING = C565(0x24, 0x33, 0x3a);
const uint16_t COL_RUN = C565(0x2d, 0xd4, 0xbf);
const uint16_t COL_STOP = C565(0xff, 0x6b, 0x6b);
const uint16_t COL_LOW = C565(0xf0, 0xa5, 0x7e);
const uint16_t COL_INK = C565(0xff, 0xff, 0xff);
const uint16_t COL_DIM = C565(0xa8, 0xbd, 0xc2);
const uint16_t COL_L_BADGE = C565(0x5e, 0xea, 0xd4);
const uint16_t COL_R_BADGE = C565(0xf0, 0xa5, 0x7e);

#if ENABLE_SCREENS
Adafruit_GC9A01A tftL(TFT_CS_L, TFT_DC, TFT_RST);  // RST on L resets both
Adafruit_GC9A01A tftR(TFT_CS_R, TFT_DC, -1);
// One shared 240x240 frame buffer (112KB). Global so it's allocated at boot
// before WiFi fragments the heap; draw a face into it, push, reuse.
GFXcanvas16 canvas(240, 240);
#endif
// False if the 112KB malloc failed. The round screens go dark, everything
// else (WiFi, phone UI, pumps, knobs) still works. Never a boot-stopper.
bool screensOk = false;

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

// In DRAM, not flash: an IRAM ISR that reads a flash-resident table crashes
// the moment it fires while flash is busy (an NVS write, an OTA).
static const DRAM_ATTR int8_t QTAB[16] = {0, -1, 1, 0, 1, 0, 0, -1,
                                          -1, 0, 0, 1, 0, 1, -1, 0};

// Per-side knob state, reported to the phone page.
enum { ENC_OFF = 0, ENC_LIVE = 1, ENC_NOISY = 2, ENC_STORM = 3 };
// A brisk human turn is a couple of hundred edges a second. Four thousand is
// not a knob, it is a floating pin, and it means the interrupt is eating the
// main loop.
const uint32_t ENC_STORM_EDGES = 4000;

struct Enc {
  uint8_t pinA, pinB, pinSW;
  volatile uint8_t prev;      // last AB state, 2 bits
  volatile int8_t quarters;   // quarter-steps banked toward a detent
  volatile int16_t detents;   // signed clicks waiting for loop() to spend
  volatile uint32_t edges;    // ISR entries this storm-guard window
  bool attached;              // interrupts actually armed on this pair
  uint8_t state;              // ENC_* above, what the page shows
  bool swDown;                // debounced switch state
  bool holdFired;             // the 1.2s hold already started this side
  unsigned long swSince;
};
Enc encs[2] = {
    {ENC_L_A, ENC_L_B, ENC_L_SW, 0, 0, 0, 0, false, ENC_OFF, false, false, 0},
    {ENC_R_A, ENC_R_B, ENC_R_SW, 0, 0, 0, 0, false, ENC_OFF, false, false, 0}};

static inline int IRAM_ATTR pinLevel(uint8_t pin) {
  return (pin < 32) ? ((REG_READ(GPIO_IN_REG) >> pin) & 1)
                    : ((REG_READ(GPIO_IN1_REG) >> (pin - 32)) & 1);
}

void IRAM_ATTR encISR(void *arg) {
  Enc *e = (Enc *)arg;
  e->edges++;  // the storm guard in loop() reads and clears this
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

// WHY THIS IS OPT-IN (2026-09-12, the build that would not boot):
// Stage 7 armed CHANGE interrupts on all four encoder lines at boot. Enc R's
// CLK/DT sit on GPIO34/35, which are input-only and have NO internal pull-up,
// so with no KY-040 plugged in they float and chatter. Two floating pins
// firing edge interrupts flat out starved loop(): no heartbeat LED, no web
// server, a dead-looking board. (Enc L on 27/26 was never the problem: its
// internal pull-ups hold it quiet when unwired.)
// So: knobs are DARK until declared wired, per side, and it sticks in NVS.
// Three layers of defence now, because a knob must never cost us a boot:
//   1. the NVS opt-in below,
//   2. a steadiness probe before the interrupts go anywhere near a pin,
//   3. a runaway-edge guard in loop() that disarms a chattering pin.
// Hardware fix worth doing anyway: a 10k pull-up to 3V3 on 34 and 35 makes
// those pins safe even with nothing plugged in.

const char *ENC_KEY[2] = {"encL", "encR"};

// A wired KY-040 holds CLK/DT at a steady level (its own 10k pull-ups; both
// HIGH at a detent). A floating pin flickers. 40ms of watching separates them.
// Takes an index, not an Enc&: the .ino preprocessor hoists prototypes above
// the struct definition, so a struct-typed parameter won't compile here.
bool encPinsSteady(int s) {
  Enc &e = encs[s];
  int a0 = digitalRead(e.pinA), b0 = digitalRead(e.pinB);
  for (int i = 0; i < 200; i++) {
    if (digitalRead(e.pinA) != a0 || digitalRead(e.pinB) != b0) return false;
    delayMicroseconds(200);
  }
  return true;
}

void encDisarm(int s, uint8_t why) {
  Enc &e = encs[s];
  if (e.attached) {
    detachInterrupt(digitalPinToInterrupt(e.pinA));
    detachInterrupt(digitalPinToInterrupt(e.pinB));
    e.attached = false;
  }
  e.detents = 0;
  e.quarters = 0;
  e.state = why;
}

bool encArm(int s) {
  Enc &e = encs[s];
  if (e.attached) return true;
  if (!encPinsSteady(s)) {  // nothing plugged in, or a bad joint
    e.state = ENC_NOISY;
    Serial.printf("Knob %c NOT armed: pins unsteady (unwired?)\n",
                  s == 0 ? 'L' : 'R');
    return false;
  }
  e.prev = (uint8_t)((digitalRead(e.pinA) << 1) | digitalRead(e.pinB));
  e.quarters = 0;
  e.detents = 0;
  e.edges = 0;
  attachInterruptArg(digitalPinToInterrupt(e.pinA), encISR, &e, CHANGE);
  attachInterruptArg(digitalPinToInterrupt(e.pinB), encISR, &e, CHANGE);
  e.attached = true;
  e.state = ENC_LIVE;
  Serial.printf("Knob %c armed\n", s == 0 ? 'L' : 'R');
  return true;
}

// Pin modes only. Safe with nothing wired: no interrupts are armed here
// unless NVS says that side's knob exists.
void encBegin() {
#if !ENABLE_KNOBS
  // Bench mode: do not even set pin modes. Nothing touches 34/35.
  encs[0].state = ENC_OFF;
  encs[1].state = ENC_OFF;
  Serial.println("    knobs compiled out (bench mode), pins left alone");
#else
  pinMode(ENC_L_A, INPUT_PULLUP);
  pinMode(ENC_L_B, INPUT_PULLUP);
  pinMode(ENC_L_SW, INPUT_PULLUP);
  pinMode(ENC_R_A, INPUT);  // 34/35 are input-only: no internal pull-up,
  pinMode(ENC_R_B, INPUT);  // the KY-040 module's own 10k resistors do it
  pinMode(ENC_R_SW, INPUT_PULLUP);
  for (int i = 0; i < 2; i++) {
    if (!prefs.getBool(ENC_KEY[i], false)) {
      encs[i].state = ENC_OFF;
      Serial.printf("Knob %c off (enable it on the page once it is wired)\n",
                    i == 0 ? 'L' : 'R');
      continue;
    }
    encArm(i);
  }
#endif
}

// Once a second: any pin firing like a floating input gets disarmed, and the
// opt-in is cleared so the next boot comes up clean rather than crippled.
void encStormGuard(unsigned long now) {
  static unsigned long win = 0;
  if (now - win < 1000) return;
  win = now;
  for (int s = 0; s < 2; s++) {
    Enc &e = encs[s];
    if (!e.attached) continue;
    noInterrupts();
    uint32_t ed = e.edges;
    e.edges = 0;
    interrupts();
    if (ed > ENC_STORM_EDGES) {
      encDisarm(s, ENC_STORM);
      prefs.putBool(ENC_KEY[s], false);
      Serial.printf("Knob %c DISARMED: %lu edges in 1s. Check its wiring.\n",
                    s == 0 ? 'L' : 'R', (unsigned long)ed);
    }
  }
}

// Spend whatever the ISR banked, and service the push switch.
void encService(int s, unsigned long now) {
  Enc &e = encs[s];
  Side &S = sides[s];
  if (!e.attached) return;  // knob not declared wired: ignore it entirely

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

float wavePhase = 0;

#if ENABLE_SCREENS

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

void drawFace(int s) {
  if (!screensOk) return;  // no frame buffer: skip the glass, keep running
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
  // coral, not teal: the liquid behind it is teal now and a teal ring on a
  // teal fill is invisible at a glance across the room.
  uint16_t ringCol = (S.running || S.done) ? COL_LOW : COL_STOP;
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
  drawCentred(pill, cx, 63, &FreeSansBold9pt7b, C565(0x06, 0x20, 0x1d));

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

#else  // ENABLE_SCREENS == 0: bench mode, the glass is compiled out
void drawFace(int s) { (void)s; }
#endif

// ---------------------------------------------------------------- web UI
// The gauge-mockup.html canvas gauges, live-fed from /status. Slider spans
// 60..100% duty: bottom of travel = 60%, everything on it is usable range.

const char PAGE[] PROGMEM = R"HTML(<!doctype html><html><head>
<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name=theme-color content="#0e1417">
<link rel=icon href="data:,">
<title>Saline Pump</title><style>
/* Lifted from Tide's design system (mission-control/src/tide/tide.css):
   one gradient voice, a dark ground, an ambient breathing glow, hairline
   sections instead of cards. Tide's voice is coral/rose; this rig runs
   teal, with coral kept as the rationed accent. */
:root{
 --grad:linear-gradient(90deg,#5eead4,#0d9488);
 --grad135:linear-gradient(135deg,#2dd4bf,#0d9488);
 --teal:#2dd4bf;--coral:#f0a57e;
 --ground:#0e1417;--ink:#e9eff1;--muted:#8ea3a8;--faint:#6d8189;
 --hair:rgba(255,255,255,.09);--input:rgba(255,255,255,.06);
 --glow-teal:rgba(45,212,191,.24);--glow-sea:rgba(56,120,160,.22)}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
 -webkit-tap-highlight-color:transparent;overflow-x:hidden}
.glow{position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:0}
.glow::before,.glow::after{content:'';position:absolute;border-radius:50%;
 filter:blur(56px);animation:breathe 14s ease-in-out infinite}
.glow::before{width:72%;height:52%;left:-16%;top:-14%;
 background:radial-gradient(circle,var(--glow-teal),transparent 70%)}
.glow::after{width:62%;height:52%;right:-12%;bottom:-16%;
 background:radial-gradient(circle,var(--glow-sea),transparent 70%);
 animation-delay:-7s}
@keyframes breathe{0%,100%{transform:scale(1);opacity:.85}
 50%{transform:scale(1.12) translate(2%,2%);opacity:1}}
.wrap{position:relative;z-index:1;max-width:640px;margin:0 auto;
 padding:20px 16px calc(104px + env(safe-area-inset-bottom))}
header{display:flex;align-items:flex-end;gap:10px;margin-bottom:6px}
.brand{flex:1;text-align:left;min-width:0}
h1{margin:0;font-size:clamp(23px,7vw,30px);font-weight:800;letter-spacing:-.02em;line-height:1.05;
 background:var(--grad);-webkit-background-clip:text;background-clip:text;
 color:transparent}
.sub{margin:5px 0 0;font-size:12.5px;color:var(--muted);
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
nav{display:flex;gap:6px;flex:none}
.pill{font-size:12.5px;font-weight:650;border-radius:999px;padding:7px 14px;
 background:transparent;border:1px solid var(--hair);color:var(--faint)}
.pill.on{background:var(--grad135);border-color:transparent;color:#06201d}
section{padding:20px 0 4px;border-top:1px solid var(--hair);margin-top:16px}
section:first-of-type{border-top:0}
.lbl{font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
 color:var(--muted);text-align:left;margin-bottom:12px}
.hint{color:var(--faint);font-size:12px;line-height:1.55;text-align:left;
 margin-top:12px}
.gauges{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.unit{width:282px;max-width:100%;padding:4px 0 14px}
.unit+.unit{border-top:1px solid var(--hair);padding-top:18px}
@media(min-width:620px){.unit+.unit{border-top:0;padding-top:4px;
 border-left:1px solid var(--hair);padding-left:15px}}
.glass{width:240px;height:240px;border-radius:50%;margin:0 auto;
 box-shadow:0 0 0 1px rgba(45,212,191,.22),0 0 0 7px #070c0e,
 0 0 0 8px rgba(255,255,255,.06),0 14px 34px rgba(0,0,0,.6),
 0 0 42px -12px rgba(45,212,191,.4);
 overflow:hidden;background:#0b1114}
canvas{display:block;width:240px;height:240px}
.row{display:grid;grid-template-columns:48px 1fr 54px;gap:10px;align-items:center;
 margin:14px 0 2px;font-size:12.5px}
.row label{text-align:left;color:var(--muted)}
.row output{text-align:right;color:var(--ink);font-variant-numeric:tabular-nums;
 font-weight:600}
input[type=range]{width:100%;height:32px;accent-color:var(--teal);background:none}
input[type=number]{width:78px;font-size:16px;background:var(--input);
 color:var(--ink);border:1px solid var(--hair);border-radius:12px;padding:9px 11px;
 text-align:right;outline:none}
input[type=number]:focus{border-color:var(--teal);
 box-shadow:0 0 0 3px rgba(45,212,191,.15)}
button{font-family:inherit;font-weight:600;border-radius:999px;
 border:1px solid var(--hair);background:transparent;color:var(--ink);
 padding:11px 14px;font-size:13px;transition:transform .12s ease}
button:active{transform:scale(.97)}
button.go{background:var(--grad135);border-color:transparent;color:#06201d}
button.warn{border-color:rgba(240,165,126,.45);color:var(--coral)}
.btns{display:flex;gap:7px;margin-top:14px}
.btns button{flex:1;padding:12px 6px}
.duo{display:flex;gap:8px;margin-bottom:8px}
.duo button{flex:1}
.calrow{display:flex;gap:9px;align-items:center;font-size:12.5px;
 color:var(--muted);margin-top:12px}
.calrow span{flex:1;text-align:left}
.stopall{position:fixed;left:16px;right:16px;
 bottom:calc(14px + env(safe-area-inset-bottom));
 background:linear-gradient(135deg,#e04a4a,#a81f1f);border:0;color:#fff;
 font-size:18px;font-weight:800;letter-spacing:.06em;padding:17px;
 border-radius:999px;box-shadow:0 10px 28px rgba(180,30,30,.36);z-index:5;
 max-width:608px;margin:0 auto}
#cnow{font-size:12.5px;color:var(--muted);margin-top:12px;text-align:left}
#cnow b,#lvls b{color:var(--ink);font-variant-numeric:tabular-nums}
#lvls{font-size:12.5px;color:var(--muted);margin-top:12px;text-align:left}
#calstate{text-align:left;font-size:12.5px;color:var(--muted);margin-bottom:14px}
#calstate .big{display:block;font-size:38px;font-weight:800;letter-spacing:-.02em;
 color:var(--coral);font-variant-numeric:tabular-nums;line-height:1.1}
#calstate.ready .big{background:var(--grad);-webkit-background-clip:text;
 background-clip:text;color:transparent}
#bench{display:none;align-items:center;gap:8px;text-align:left;
 border:1px solid rgba(240,165,126,.35);background:rgba(240,165,126,.07);
 color:var(--coral);border-radius:14px;padding:10px 13px;margin-top:16px;
 font-size:12px;line-height:1.45}
#toast{position:fixed;left:16px;right:16px;
 bottom:calc(84px + env(safe-area-inset-bottom));max-width:608px;margin:0 auto;
 background:rgba(13,148,136,.16);border:1px solid rgba(45,212,191,.4);
 color:#bdf4ea;border-radius:14px;padding:11px 13px;font-size:13px;
 opacity:0;transition:opacity .25s;pointer-events:none;z-index:6}
</style></head><body>
<div class=glow></div>
<div class=wrap>
<header><div class=brand><h1>Saline Pump</h1><p class=sub id=sub>connecting&hellip;</p></div>
<nav><button class="pill on" id=tab0 onclick=show(0)>Run</button>
<button class=pill id=tab1 onclick=show(1)>Settings</button></nav></header>
<div id=bench></div>
<div id=v0>
<section><div class=gauges id=g></div>
<div class=hint>Speed runs 60-100%: the heads stall below about 55%, so the
bottom of the slider is the slowest they will actually turn. Delivered volume
is an estimate until the flow calibration is done, over in Settings.</div>
</section></div>
<div id=v1 style=display:none>
<section><div class=lbl>Flow calibration</div>
<div id=calstate>Not running.</div>
<div class=duo>
<button class=warn onclick="act('/cal?side=L',{L:{cal:1,calEnd:Date.now()+60000}})">Calibrate L</button>
<button class=warn onclick="act('/cal?side=R',{R:{cal:1,calEnd:Date.now()+60000}})">Calibrate R</button></div>
<div class=calrow><span>ml caught in 60s</span>
<input type=number id=cm min=5 max=400 step=.1 placeholder=ml>
<button class=go onclick=saveCal()>Save</button></div>
<div id=cnow>using <b>?</b> ml/min at 100%</div>
<div class=hint>Prime the line, put the outlet in a measuring jug, hit
Calibrate. That head runs wide open for exactly 60 seconds and counts down
above. Type the ml you caught and Save: it is stored on the board and
survives a reboot or an OTA push. Tap Calibrate again mid-run to abandon it.</div>
</section>
<section><div class=lbl>Reservoir &amp; run</div>
<div class=duo>
<button onclick="act('/refill?side=L')">L refilled</button>
<button onclick="act('/refill?side=R')">R refilled</button></div>
<div class=duo>
<button onclick="act('/reset?side=L')">Reset L run</button>
<button onclick="act('/reset?side=R')">Reset R run</button></div>
<div id=lvls>reservoirs: L <b>?</b> &middot; R <b>?</b></div>
<div class=hint>Refilled tells the rig that side's bag is full again. Reset
run zeroes delivered ml and the clock, ready for the next dose.</div>
</section>
<section id=knobcard><div class=lbl>Knobs</div>
<div class=duo>
<button id=kL onclick=knob('L')>L knob: ?</button>
<button id=kR onclick=knob('R')>R knob: ?</button></div>
<div class=hint>Turn one on only once its KY-040 is actually wired. Enc R sits
on GPIO34/35, which have no internal pull-ups: unwired they chatter, and the
interrupts starve the board. It refuses to arm on a floating pin and disarms
itself if one starts storming. Turn = speed, short press = stop that side,
hold 1.2s = start.</div>
</section>
<section><div class=lbl>Safety</div>
<div class=hint>Prime auto-stops after 10 seconds and does not count toward
the dose. Firmware caps, independent of this page: 600 ml a run, 90 minutes,
and a low-reservoir stop so a primed line never pumps air. The stall floor
clamps a too-low request upward rather than letting a head sit buzzing.
STOP ALL and the physical E-stop kill both pumps regardless of anything
here.</div>
</section></div>
</div>
<div id=toast></div>
<button class=stopall onclick="act('/stop',{L:{run:0,prime:0,cal:0},R:{run:0,prime:0,cal:0}})">STOP ALL</button>
<script>
const TAU=Math.PI*2,SIDES=['L','R'],$=i=>document.getElementById(i);
// Backing store at device resolution: a 240x240 canvas upscaled by the
// browser is why the big number looked like a fax. Capped at 2x, which is
// crisp on a 3x phone screen without quadrupling the fill cost.
const DPR=Math.min(2,window.devicePixelRatio||1);
const C={slateTop:'#101a1d',slateBot:'#0a1013',deep:'#07443f',mid:'#0d9488',
 surf:'#2dd4bf',foam:'#b6f5ea',ring:'#24333a',run:'#2dd4bf',stop:'#ff6b6b',
 warn:'#f0a57e',ink:'#fff',dim:'rgba(233,239,241,.7)',
 badgeL:'#5eead4',badgeR:'#f0a57e'};
const KST={0:'off',1:'ON',2:'no signal',3:'disarmed (noise)'};
let editing={},view=0,MLMIN=100,CAP=1000,calDone='',hot=0,timer=0,tt=0;

function card(s){return `<div class=unit>
<div class=glass><canvas id=c${s}></canvas></div>
<div class=row><label>Speed</label>
<input type=range min=60 max=100 step=1 value=70 id=s${s}
 onpointerdown="editing['s${s}']=1"
 oninput="o${s}.textContent=this.value+'%';G.${s}.st.duty=+this.value"
 onpointerup="editing['s${s}']=0;send('${s}')"
 onchange="editing['s${s}']=0;send('${s}')"><output id=o${s}>70%</output></div>
<div class=row><label>Target</label>
<input type=number min=10 max=600 step=10 value=120 id=t${s}
 onfocus="editing['t${s}']=1" onblur="editing['t${s}']=0"
 onchange="send('${s}')" style=justify-self:start><output>ml</output></div>
<div class=btns>
<button class=go onclick="act('/run?side=${s}&amp;on=1',{${s}:{run:1,done:0,low:0}})">Start</button>
<button onclick="act('/run?side=${s}&amp;on=0',{${s}:{run:0,prime:0}})">Stop</button>
<button class=warn onclick="act('/prime?side=${s}')">Prime</button>
</div></div>`}
$('g').innerHTML=card('L')+card('R');

function roundRect(x,y,w,h,r,ctx){ctx.beginPath();ctx.moveTo(x+r,y);
 ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);
 ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath()}
function fmtT(s){const m=Math.floor(s/60),ss=Math.floor(s%60);
 return String(m).padStart(2,'0')+':'+String(ss).padStart(2,'0')}
function calLeft(s){const g=G[s].st;
 return g.cal?Math.max(0,Math.ceil(((g.calEnd||0)-Date.now())/1000)):0}

function gauge(side){
 const cv=$('c'+side);cv.width=Math.round(240*DPR);cv.height=Math.round(240*DPR);
 const ctx=cv.getContext('2d');ctx.scale(DPR,DPR);
 const st={lvl:1,duty:70,run:0,prime:0,done:0,low:0,cal:0,calEnd:0,
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
  const act=(st.run||st.prime||st.cal)?1:.35,a1=5.5,a2=3;
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
  if(frac>.002){ctx.strokeStyle=(st.run||st.done)?C.warn:C.stop;
   ctx.beginPath();ctx.arc(cx,cy,rr,-Math.PI/2,-Math.PI/2+frac*TAU);ctx.stroke()}
  ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.shadowColor='rgba(0,0,0,.55)';ctx.shadowBlur=6;
  ctx.font='700 13px -apple-system,Segoe UI,Roboto,sans-serif';
  ctx.fillStyle=side==='L'?C.badgeL:C.badgeR;
  ctx.fillText(side==='L'?'LEFT':'RIGHT',cx,40);
  const pill=st.cal?'CAL':st.prime?'PRIME':st.run?'RUN':st.low?'LOW'
   :st.done?'DONE':'STOP';
  const pcol=(st.cal||st.prime||st.low)?C.warn:(st.run||st.done)?C.run:C.stop;
  ctx.font='700 11px -apple-system,Segoe UI,Roboto,sans-serif';
  const pw=ctx.measureText(pill).width+18;
  ctx.shadowBlur=0;ctx.fillStyle=pcol;
  roundRect(cx-pw/2,52,pw,20,10,ctx);ctx.fill();
  ctx.fillStyle='#06201d';ctx.fillText(pill,cx,62.5);
  ctx.shadowColor='rgba(0,0,0,.55)';ctx.shadowBlur=6;
  ctx.fillStyle=C.ink;
  ctx.font='800 54px -apple-system,Segoe UI,Roboto,sans-serif';
  ctx.fillText(String(Math.round(st.duty)),cx,cy+2);
  ctx.font='600 14px -apple-system,Segoe UI,Roboto,sans-serif';
  ctx.fillStyle=C.dim;ctx.fillText('speed %',cx,cy+34);
  ctx.font='700 16px -apple-system,Segoe UI,Roboto,sans-serif';
  if(st.cal){ctx.fillStyle=C.warn;
   ctx.fillText('CATCH IT: '+calLeft(side)+'s',cx,cy+64);
   ctx.font='600 13px -apple-system,Segoe UI,Roboto,sans-serif';
   ctx.fillStyle=C.dim;ctx.fillText('into the jug',cx,cy+84)}
  else{ctx.fillStyle=C.ink;
   ctx.fillText(Math.round(st.del)+' / '+Math.round(st.tgt)+' ml',cx,cy+64);
   ctx.font='600 13px -apple-system,Segoe UI,Roboto,sans-serif';
   ctx.fillStyle=C.dim;ctx.fillText(fmtT(st.el),cx,cy+84)}
  ctx.shadowBlur=0}
 // Between polls the numbers keep moving locally off the known flow rate, so
 // nothing sits frozen waiting for the next /status. The poll corrects it.
 return {st,tick:dt=>{t+=dt;
  if(st.run||st.prime||st.cal){
   const ml=MLMIN*(st.duty/100)*(dt/60);
   st.lvl=Math.max(0,st.lvl-ml/CAP);
   if(st.run){st.del+=ml;st.el+=dt}}
  draw()}}}
const G={L:gauge('L'),R:gauge('R')};

// ---- one request at a time -------------------------------------------
// The ESP32's WebServer serves exactly one client at a time, so overlapping
// fetches queue up in the TCP backlog and everything feels like treacle.
// All traffic goes through this queue; a button tap jumps in front of a poll.
let busy=false,q=[];
async function fetchJSON(u){
 const ac=new AbortController(),to=setTimeout(()=>ac.abort(),4000);
 try{return await(await fetch(u,{cache:'no-store',signal:ac.signal})).json()}
 catch(e){return null}finally{clearTimeout(to)}}
function req(u,front){return new Promise(res=>{
 const it={u,res};front?q.unshift(it):q.push(it);drain()})}
async function drain(){if(busy||!q.length)return;busy=true;
 const it=q.shift();const j=await fetchJSON(it.u);
 busy=false;it.res(j);drain()}

function active(){return SIDES.some(s=>{const d=G[s].st;
 return d.run||d.prime||d.cal})}
function schedule(){clearTimeout(timer);
 let ms=active()?400:1500;
 if(Date.now()<hot)ms=250;
 timer=setTimeout(poll,ms)}
async function poll(){clearTimeout(timer);
 if(!busy&&!q.length){const j=await req('/status');if(j)apply(j)}
 schedule()}
// Optimistic patch first so the glass reacts on the tap, then the board's own
// answer (every endpoint returns the full status) lands in the same round trip.
async function act(u,patch){
 if(patch)for(const s in patch)Object.assign(G[s].st,patch[s]);
 calText();hot=Date.now()+2500;
 const j=await req(u,true);if(j)apply(j);
 schedule();return j}

function toast(m){const e=$('toast');e.textContent=m;e.style.opacity=1;
 clearTimeout(tt);tt=setTimeout(()=>e.style.opacity=0,2800)}

function calText(){const el=$('calstate'),s=SIDES.find(x=>G[x].st.cal);
 if(s){el.className='';
  el.innerHTML='<b class=big>'+calLeft(s)+'s</b>Side '+s
   +' is running wide open. Catch it in the jug.'}
 else if(calDone){el.className='ready';
  el.innerHTML='<b class=big>Done</b>Side '+calDone
   +' finished. Measure the jug and type the ml below.'}
 else{el.className='';
  el.textContent='Not running. Calibrate a side to measure its real flow.'}}

function apply(j){
 MLMIN=j.mlmin;CAP=j.cap||1000;
 for(const s of SIDES){const d=j[s],g=G[s].st;
  if(g.cal&&!d.cal){calDone=s;
   if(view==0)toast('Side '+s+' calibration done, enter the ml in Settings.')}
  if(d.cal)calDone='';
  g.lvl=d.lvl;g.run=d.run;g.prime=d.prime;g.done=d.done;g.low=d.low;
  g.cal=d.cal;g.calEnd=d.cal?Date.now()+d.calleft*1000:0;
  g.del=d.del;g.tgt=d.tgt;g.el=d.el;
  g.duty=(d.run||d.prime||d.cal)?d.duty:d.req;
  if(!editing['s'+s]){$('s'+s).value=d.req;$('o'+s).textContent=d.req+'%'}
  if(!editing['t'+s])$('t'+s).value=Math.round(d.tgt);
  const kb=$('k'+s);kb.dataset.on=(d.enc==1)?'1':'0';
  kb.textContent=s+' knob: '+KST[d.enc];
  kb.className=(d.enc==1)?'go':(d.enc?'warn':'')}
 $('knobcard').style.display=j.knobs?'':'none';
 const bm=$('bench'),off=[];
 if(!j.knobs)off.push('knobs');
 if(!j.screens)off.push('screens');
 bm.style.display=off.length?'flex':'none';
 bm.textContent='Bench mode: '+off.join(' and ')+' compiled out of this build.'
  +' Both pumps, the firmware caps and the E-stop are all still live.';
 $('cnow').innerHTML='using <b>'+j.mlmin.toFixed(1)+'</b> ml/min at 100%';
 $('lvls').innerHTML='reservoirs: L <b>'+Math.round(j.L.lvl*100)
  +'%</b> &middot; R <b>'+Math.round(j.R.lvl*100)+'%</b>';
 const bits=SIDES.map(s=>{const d=j[s];
  return s+' '+(d.cal?'calibrating':d.prime?'priming':d.run?'running'
   :d.low?'low':d.done?'done':'idle')});
 $('sub').textContent=bits.join('  ·  ')+'  ·  '
  +j.mlmin.toFixed(0)+' ml/min';
 calText();
 if(j.msg)toast(j.msg)}

function show(v){view=v;
 $('v0').style.display=v?'none':'';$('v1').style.display=v?'':'none';
 $('tab0').className='pill'+(v?'':' on');$('tab1').className='pill'+(v?' on':'');
 window.scrollTo(0,0);hot=Date.now()+1200;poll()}
function send(s){act('/set?side='+s+'&duty='+$('s'+s).value
 +'&target='+$('t'+s).value)}
async function saveCal(){const v=$('cm').value;
 if(!v){toast('Type the ml you caught first.');return}
 const j=await act('/calsave?ml='+encodeURIComponent(v));
 if(j&&Math.abs(j.mlmin-parseFloat(v))<.05){$('cm').value='';calDone='';calText()}}
async function knob(s){const b=$('k'+s);
 await act('/enc?side='+s+'&on='+(b.dataset.on=='1'?0:1))}

document.addEventListener('visibilitychange',()=>{
 if(!document.hidden){hot=Date.now()+1200;poll()}});
// Frame budget: 30fps while something is moving, 10fps idle, nothing at all
// on the settings tab or a hidden page. The old loop redrew two faces at
// 60fps forever, which is what made touch feel sticky.
let last=performance.now(),acc=0;
(function frame(){requestAnimationFrame(frame);
 const now=performance.now(),dt=Math.min(.05,(now-last)/1000);last=now;
 if(view!=0||document.hidden)return;
 acc+=dt;const step=active()?1/30:1/10;
 if(acc<step)return;
 G.L.tick(acc);G.R.tick(acc);acc=0})();
setInterval(calText,250);
calText();poll();
</script></body></html>)HTML";

int sideArg() { return (server.arg("side") == "R") ? 1 : 0; }

// Whole seconds left on a calibration run, 0 when there isn't one.
long calLeft(int s) {
  if (!sides[s].calibrating) return 0;
  long ms = (long)(sides[s].calUntil - millis());
  return ms > 0 ? (ms + 999) / 1000 : 0;
}

// EVERY endpoint answers with the full status blob, not "ok". The phone page
// talks to a server that handles one client at a time, so a command that
// needed a second round trip to find out what it did was the single biggest
// source of the UI feeling laggy. One request in, fresh truth out.
// msg, if given, is shown as a toast on the page: keep it quote-free.
void sendStatus(const char *msg = nullptr, int code = 200) {
  char buf[1100];
  int n = snprintf(buf, sizeof buf,
                   "{\"mlmin\":%.1f,\"cap\":%.0f,\"knobs\":%d,\"screens\":%d,"
                   "\"msg\":\"%s\",",
                   mlPerMin100, RES_CAPACITY, ENABLE_KNOBS ? 1 : 0,
                   screensOk ? 1 : 0, msg ? msg : "");
  for (int s = 0; s < 2; s++) {
    Side &S = sides[s];
    n += snprintf(buf + n, sizeof buf - n,
                  "\"%c\":{\"run\":%d,\"prime\":%d,\"done\":%d,\"low\":%d,"
                  "\"cal\":%d,\"calleft\":%ld,\"enc\":%d,"
                  "\"req\":%d,\"duty\":%d,\"tgt\":%.0f,\"del\":%.1f,"
                  "\"el\":%.0f,\"lvl\":%.3f}%s",
                  s == 0 ? 'L' : 'R', S.running, S.priming, S.done, S.lowStop,
                  S.calibrating, calLeft(s), encs[s].state,
                  dutyFor(s), S.actualDuty, S.target, S.delivered, S.elapsedS,
                  S.remain / RES_CAPACITY, s == 0 ? "," : "}");
  }
  server.send(code, "application/json", buf);
}

void handleStatus() { sendStatus(); }

void handleSet() {
  int s = sideArg();
  Side &S = sides[s];
  if (server.hasArg("duty"))
    S.dutyReq = constrain(server.arg("duty").toInt(), UI_MIN_DUTY, 100);
  if (server.hasArg("target"))
    S.target = constrain(server.arg("target").toFloat(), 10.0f, MAX_TARGET);
  applyDuty(s);  // live speed change if it's already turning
  sendStatus();
}

void handleRun() {
  int s = sideArg();
  if (server.arg("on") == "1") startRun(s);
  else stopRun(s);
  sendStatus();
}

void handlePrime() {
  int s = sideArg();
  Side &S = sides[s];
  if (S.running || S.calibrating) {
    sendStatus("Stop that side first.", 409);
    return;
  }
  if (S.priming) {  // second tap = stop priming
    stopRun(s);
  } else if (S.remain > RES_LOW_STOP) {
    S.priming = true;
    S.lowStop = false;
    S.primeUntil = millis() + PRIME_MAX_MS;
    pumpWrite(s, 100);
  } else {
    sendStatus("That reservoir is empty. Refill it in Settings.", 409);
    return;
  }
  sendStatus();
}

void handleReset() {
  int s = sideArg();
  stopRun(s);
  sides[s].delivered = 0;
  sides[s].elapsedS = 0;
  sides[s].done = false;
  sides[s].lowStop = false;
  sendStatus(s == 0 ? "Left run reset." : "Right run reset.");
}

void handleRefill() {
  int s = sideArg();
  sides[s].remain = RES_CAPACITY;
  sides[s].lowStop = false;
  sendStatus(s == 0 ? "Left reservoir marked full." : "Right reservoir marked full.");
}

// Start the 60s wide-open run into a measuring jug. Refuses if that side
// is doing anything else, so a cal can never be layered over a real dose.
void handleCal() {
  int s = sideArg();
  Side &S = sides[s];
  if (S.calibrating) {  // second tap = abandon it
    stopRun(s);
    sendStatus("Calibration abandoned.");
    return;
  }
  if (S.running || S.priming) {
    sendStatus("Stop that side first.", 409);
    return;
  }
  S.calibrating = true;
  S.lowStop = false;
  S.calUntil = millis() + CAL_MS;
  pumpWrite(s, 100);
  Serial.printf("Calibration run %c: 60s at 100%%\n", s == 0 ? 'L' : 'R');
  sendStatus();
}

// The measured ml caught in 60s IS the ml/min figure. Persisted to NVS so
// it survives a reboot or an OTA push.
void handleCalSave() {
  float ml = server.arg("ml").toFloat();
  if (ml < CAL_MIN || ml > CAL_MAX) {
    sendStatus("That is outside 5-400 ml, check what you typed.", 400);
    return;
  }
  mlPerMin100 = ml;
  prefs.putFloat("mlmin", mlPerMin100);
  Serial.printf("Calibrated: %.1f ml/min at 100%%\n", mlPerMin100);
  sendStatus("Calibrated. Every volume now scales off that.");
}

// Declare a side's knob wired (or not). Persisted, so it survives reboots.
void handleEnc() {
#if !ENABLE_KNOBS
  sendStatus("Knobs are compiled out of this build.");
  return;
#else
  int s = sideArg();
  bool on = (server.arg("on") == "1");
  if (!on) {
    encDisarm(s, ENC_OFF);
    prefs.putBool(ENC_KEY[s], false);
    sendStatus();
    return;
  }
  if (!encArm(s)) {  // refuse rather than arm an interrupt on a floating pin
    prefs.putBool(ENC_KEY[s], false);
    sendStatus("Those pins are floating. Check the KY-040 wiring (GND, 3V3, "
               "CLK, DT, SW) before enabling it.");
    return;
  }
  prefs.putBool(ENC_KEY[s], true);
  sendStatus();
#endif
}

// ---------------------------------------------------------------- setup

void setup() {
  // FIRST lines, before serial, before anything: gates off (GPIO14 twitch).
  pinMode(PUMP_L_GATE, OUTPUT);
  digitalWrite(PUMP_L_GATE, LOW);
  pinMode(PUMP_R_GATE, OUTPUT);
  digitalWrite(PUMP_R_GATE, LOW);

#if ENABLE_SCREENS
  pinMode(TFT_CS_L, OUTPUT);
  digitalWrite(TFT_CS_L, HIGH);
  pinMode(TFT_CS_R, OUTPUT);
  digitalWrite(TFT_CS_R, HIGH);
#endif
  pinMode(LED, OUTPUT);

  // Serial before anything that can hang, so a hang has already identified
  // itself by the time it happens.
  Serial.begin(115200);
  delay(400);
  Serial.println();
  Serial.println("=====================================================");
  Serial.printf("Saline Pump  STAGE 7d   built %s %s\n", __DATE__, __TIME__);
  Serial.printf("BENCH MODE: screens %s, knobs %s\n",
                ENABLE_SCREENS ? "IN" : "compiled out",
                ENABLE_KNOBS ? "IN" : "compiled out");
  Serial.println("If you cannot see this line, the board is not running");
  Serial.println("this binary: the upload did not take.");
  Serial.printf("reset reason: %d  (1=power-on 3=sw 4=panic 5-7=watchdog)\n",
                (int)esp_reset_reason());
  Serial.printf("heap: %u free, %u largest block, %u at boot\n",
                (unsigned)ESP.getFreeHeap(),
                (unsigned)ESP.getMaxAllocHeap(),
                (unsigned)ESP.getHeapSize());
  Serial.println("Pumps start OFF.");
  Serial.println("=====================================================");

  // 1.5s of unmissable blinking = "I reached setup()". The old version was
  // three 60ms flickers and you could blink and miss the lot.
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED, HIGH);
    delay(250);
    digitalWrite(LED, LOW);
    delay(250);
  }

  // The frame buffer is 112KB in one contiguous lump and it is the single
  // most likely thing on this board to fail an allocation. It is NOT allowed
  // to stop the boot any more.
#if ENABLE_SCREENS
  screensOk = (canvas.getBuffer() != nullptr);
  if (!screensOk) {
    Serial.println("!! frame buffer alloc FAILED: round screens disabled,");
    Serial.println("!! everything else (WiFi, phone UI, pumps) carries on.");
  }
#else
  screensOk = false;
  Serial.println("Screens compiled out: no 112KB frame buffer, ~112KB more");
  Serial.println("heap, and loop() does no drawing at all.");
#endif

  Serial.println("[1] PWM");
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

  Serial.println("[2] NVS");
  prefs.begin("pump", false);
  sides[0].minPct = prefs.getInt("minL", 0);  // stall floors from Stage 5
  sides[1].minPct = prefs.getInt("minR", 0);
  mlPerMin100 = prefs.getFloat("mlmin", 100.0f);
  Serial.printf("Stall floors: L=%d%% R=%d%% (UI floor %d%%)\n",
                sides[0].minPct, sides[1].minPct, UI_MIN_DUTY);
  Serial.printf("Flow: %.1f ml/min at 100%%%s\n", mlPerMin100,
                prefs.isKey("mlmin") ? "" : "  <-- UNCALIBRATED, guess");

  Serial.println("[3] knobs");
  encBegin();

  Serial.println("[4] SPI + screens");
#if ENABLE_SCREENS
  if (screensOk) {
    SPI.begin(TFT_SCK, -1, TFT_MOSI, -1);
    tftL.begin(27000000);
    tftR.begin(27000000);
    drawFace(0);
    drawFace(1);
  } else {
    Serial.println("    skipped, no frame buffer");
  }
#else
  Serial.println("    skipped, screens compiled out (bench mode)");
#endif

  // WiFi. The old one-shot 15s window then AP-forever stranded the board
  // after an OTA reboot (2026-09-11): first reconnect after a soft reset
  // can miss the window, and there was no way back without a power cycle.
  // Now: AP_STA fallback, and loop() keeps retrying the house WiFi from
  // AP mode; on success the AP is torn down.
  Serial.println("[5] WiFi (up to 20s)");
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

  Serial.println("[6] OTA");
  ArduinoOTA.setHostname("salinepump");
  ArduinoOTA.setPassword("primefirst");
  ArduinoOTA.onStart([]() {
    stopAll();
    Serial.println("OTA starting, pumps forced off");
  });
  ArduinoOTA.begin();

  Serial.println("[7] HTTP");
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
  server.on("/enc", handleEnc);
  server.on("/status", handleStatus);
  server.begin();
  Serial.println("[8] BOOT COMPLETE, entering loop()");
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
  encStormGuard(now);

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

#if ENABLE_SCREENS
  // redraw: one face per tick, alternating, so the loop never stalls long
  static unsigned long lastDraw = 0;
  static int drawSide = 0;
  if (now - lastDraw >= 40) {
    lastDraw = now;
    wavePhase += 0.06f;
    drawFace(drawSide);
    drawSide = 1 - drawSide;
  }
#endif

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

  // Serial heartbeat: proof loop() is alive, and what the network is doing.
  // Ten seconds apart so it never drowns anything useful.
  static unsigned long lastBeat = 0;
  if (now - lastBeat >= 10000) {
    lastBeat = now;
    Serial.printf("alive %lus  heap %u  wifi %s  %s  screens %s\n", now / 1000,
                  (unsigned)ESP.getFreeHeap(),
                  WiFi.status() == WL_CONNECTED ? "STA" : (apFallback ? "AP" : "--"),
                  WiFi.status() == WL_CONNECTED
                      ? WiFi.localIP().toString().c_str()
                      : "no-ip",
                  screensOk ? "on" : (ENABLE_SCREENS ? "FAILED" : "bench-off"));
  }

  // LED: solid while any pump runs, short heartbeat blink when idle
  bool anyRun = sides[0].running || sides[1].running || sides[0].priming ||
                sides[1].priming || sides[0].calibrating || sides[1].calibrating;
  digitalWrite(LED, anyRun ? HIGH : ((now % 1000) < 80 ? HIGH : LOW));

  ArduinoOTA.handle();
  server.handleClient();
}
