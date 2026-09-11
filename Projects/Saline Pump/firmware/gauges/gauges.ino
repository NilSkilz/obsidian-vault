// Saline Pump v1 — Stage 6: the gauge UI, on real glass.
//
// Ports the gauge-mockup.html design (vault: Projects/Saline Pump/) onto the
// two GC9A01 round displays: reservoir level as a liquid fill with a moving
// two-sine surface, dose-progress ring around the rim, big live ml/min in the
// middle, delivered/target and elapsed time below, RUN/STOP/DONE/LOW pill up
// top. LEFT face cyan-badged, RIGHT orange, matching the bring-up sketch.
//
// This stage replaces raw duty control with DOSING:
//   - set a rate (ml/min) and a target volume (ml) per side, hit Start,
//     the pump stops itself at the target. Set-and-go, per the overview.
//   - PRIME button per side: 100% for line purging, 10s auto-off, only
//     allowed while that side is not running. Prime volume drains the
//     reservoir estimate but does NOT count toward the dose.
//   - reservoir level is ESTIMATED by integrating flow (no HX711 yet).
//     Refill button resets it to full. Load cells replace this in a later
//     stage.
//
// ── CALIBRATION, DO THIS BEFORE ANY REAL RUN ─────────────────────────────
// ML_PER_MIN_AT_100 below is the pump's flow at 100% duty and is currently
// the datasheet-ish guess (~100 ml/min for a 500-series head at 12V). Wet
// test: prime the line, run one pump at 100% into a measuring jug for
// exactly 60s, type the ml you got into ML_PER_MIN_AT_100, reflash. Every
// rate, dose and level number scales off this one constant.
// ─────────────────────────────────────────────────────────────────────────
//
// Safety carried over / added:
//   - gates forced LOW as the first lines of setup() (GPIO14 boot-twitch).
//   - stall limits from Stage 5 persist (NVS): a requested rate whose duty
//     lands below the stall floor is clamped UP and the screen shows the
//     rate you're actually getting, not the one you asked for.
//   - kick-start (250ms at 100%) retained; the kick's extra ml is counted.
//   - firmware hard caps: MAX_RATE / MAX_TARGET, independent of the UI.
//   - low-reservoir auto-stop so a primed line never pumps air.
//   - 90 min absolute run timeout. OTA forces pumps off. E-stop unchanged.
//
// Libraries: Adafruit GC9A01A (+ GFX, BusIO), same as Stage 5.
// Board: ESP32 DevKitC 30-pin, PCB v1 locked pin map (2026-08-20):
//   GPIO14 = Pump L gate   GPIO13 = Pump R gate   GPIO2 = onboard LED
//   Displays (shared SPI): MOSI=23 SCK=18 DC=19 RST=15, CS L=5 / R=4
// Encoders (27/26/25 + 34/35/32) are wired on the PCB but not read yet;
// they land in Stage 7 as rate knobs + push-to-stop.

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

// ---- flow model ----
const float ML_PER_MIN_AT_100 = 100.0;  // CALIBRATE WET (see header)
const float MAX_RATE = 50.0;            // ml/min, firmware cap
const float MAX_TARGET = 600.0;         // ml per run, firmware cap
const float RES_CAPACITY = 1000.0;      // ml, one saline bag/bottle per side
const float RES_LOW_STOP = 30.0;        // stop before the line sucks air
const unsigned long MAX_RUN_MS = 90UL * 60UL * 1000UL;
const unsigned long PRIME_MAX_MS = 10000;

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

struct Side {
  bool running = false;
  bool priming = false;
  bool done = false;     // reached target
  bool lowStop = false;  // reservoir guard tripped
  float rateReq = 17.0;  // what was asked for (ml/min)
  float target = 120.0;  // ml
  float delivered = 0;   // ml, this run
  float remain = RES_CAPACITY;
  float elapsedS = 0;
  int minPct = 0;              // stall floor from Stage 5 (NVS)
  int actualDuty = 0;          // what LEDC is holding right now
  unsigned long kickUntil = 0;
  int kickTarget = 0;
  unsigned long primeUntil = 0;
  unsigned long runStartMs = 0;
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

// The duty a requested rate wants, clamped up to the stall floor. Returns
// the duty; *effRate gets the rate that duty actually delivers.
int dutyForRate(int s, float rate, float *effRate) {
  int duty = (int)ceilf(rate / ML_PER_MIN_AT_100 * 100.0f);
  duty = constrain(duty, 0, 100);
  if (duty > 0 && duty < sides[s].minPct) duty = sides[s].minPct;
  if (effRate) *effRate = duty * ML_PER_MIN_AT_100 / 100.0f;
  return duty;
}

void startRun(int s) {
  Side &S = sides[s];
  if (S.priming) return;
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
  int duty = dutyForRate(s, S.rateReq, nullptr);
  S.running = true;
  S.runStartMs = millis();
  if (duty < KICK_PCT_MAX) {
    pumpWrite(s, 100);
    S.kickUntil = millis() + KICK_MS;
    S.kickTarget = duty;
  } else {
    pumpWrite(s, duty);
  }
  Serial.printf("Run %c: %.1f ml/min -> duty %d%%, target %.0f ml\n",
                s == 0 ? 'L' : 'R', S.rateReq, duty, S.target);
}

void stopRun(int s) {
  Side &S = sides[s];
  S.running = false;
  S.priming = false;
  S.kickUntil = 0;
  S.primeUntil = 0;
  pumpWrite(s, 0);
}

void stopAll() {
  stopRun(0);
  stopRun(1);
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
  uint16_t ringCol = S.running ? COL_RUN : (S.done ? COL_RUN : COL_STOP);
  if (frac > 0.002f) arcRing(cx, cy, 111, 3, top, top + frac * TAU, ringCol);

  // side badge (top)
  drawCentred(s == 0 ? "LEFT" : "RIGHT", cx, 38, &FreeSansBold9pt7b,
              s == 0 ? COL_L_BADGE : COL_R_BADGE);

  // state pill
  const char *pill = S.priming ? "PRIME"
                   : S.running ? "RUN"
                   : S.lowStop ? "LOW"
                   : S.done    ? "DONE"
                               : "STOP";
  uint16_t pillCol = S.priming ? COL_LOW
                   : S.running ? COL_RUN
                   : S.lowStop ? COL_LOW
                   : S.done    ? COL_RUN
                               : COL_STOP;
  int16_t x1, y1;
  uint16_t tw, th;
  canvas.setFont(&FreeSansBold9pt7b);
  canvas.getTextBounds(pill, 0, 0, &x1, &y1, &tw, &th);
  canvas.fillRoundRect(cx - tw / 2 - 9, 52, tw + 18, 22, 11, pillCol);
  drawCentred(pill, cx, 63, &FreeSansBold9pt7b, C565(0x08, 0x11, 0x0d));

  // big number: the rate actually being delivered (post stall-floor clamp)
  float effRate;
  dutyForRate(s, S.rateReq, &effRate);
  float shown = (S.running || S.priming)
                    ? S.actualDuty * ML_PER_MIN_AT_100 / 100.0f
                    : effRate;
  char buf[16];
  snprintf(buf, sizeof buf, "%.0f", shown);
  drawCentred(buf, cx, cy + 2, &FreeSansBold24pt7b, COL_INK);
  drawCentred("ml / min", cx, cy + 34, &FreeSans9pt7b, COL_DIM);

  // dose + time (bottom)
  snprintf(buf, sizeof buf, "%.0f / %.0f ml", S.delivered, S.target);
  drawCentred(buf, cx, cy + 62, &FreeSansBold9pt7b, COL_INK);
  int m = (int)(S.elapsedS / 60), sec = (int)S.elapsedS % 60;
  snprintf(buf, sizeof buf, "%02d:%02d", m, sec);
  drawCentred(buf, cx, cy + 84, &FreeSans9pt7b, COL_DIM);

  Adafruit_GC9A01A &tft = (s == 0) ? tftL : tftR;
  tft.drawRGBBitmap(0, 0, canvas.getBuffer(), 240, 240);
}

// ---------------------------------------------------------------- web UI

const char PAGE[] PROGMEM = R"HTML(<!doctype html><html><head>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Saline Pump</title><style>
body{background:#0c0f14;color:#e7edf3;font-family:-apple-system,sans-serif;margin:14px;text-align:center}
h1{font-size:1.1em;color:#8aa0b3;font-weight:600}
.pump{border:1px solid #202a35;background:#141a22;border-radius:14px;padding:12px;margin:12px 0}
.pump h2{margin:2px 0 8px;font-size:1.05em}
.L h2{color:#0ff}.R h2{color:#f90}
.big{font-size:1.7em;font-weight:700;margin:4px 0}
.sub{color:#8aa0b3;font-size:.85em;margin:2px 0 8px}
.row{display:flex;align-items:center;gap:8px;margin:8px 0;font-size:.9em}
.row label{width:52px;text-align:left;color:#8aa0b3}
.row output{width:74px;text-align:right;font-variant-numeric:tabular-nums}
input[type=range]{flex:1;height:30px}
input[type=number]{width:70px;font-size:1em;background:#1d2732;color:#e7edf3;border:1px solid #2c3948;border-radius:8px;padding:6px}
button{font-size:.95em;padding:10px 12px;margin:3px;border:0;border-radius:10px;background:#1d2732;color:#e7edf3;border:1px solid #2c3948}
button.go{background:#1d5c46;border-color:#2a8666}
button.warn{background:#5c4a1d;border-color:#866f2a}
.stop{background:#a00;border:0;color:#fff;font-size:1.25em;width:100%;padding:16px;margin-top:6px;border-radius:12px}
small{color:#667}
</style></head><body>
<h1>Saline Pump</h1>
<div id=cards></div>
<button class=stop onclick="fetch('/stop')">STOP ALL</button>
<p><small>Rates/volumes are estimates until the flow calibration is done
(ML_PER_MIN_AT_100). Prime auto-stops after 10s. A rate below the stall
floor is bumped up to it and the real rate is shown. E-stop kills pumps
regardless of anything on this page.</small></p>
<script>
const SIDES=['L','R'];let editing={};
function card(s){return `<div class="pump ${s}"><h2>${s=='L'?'LEFT':'RIGHT'}</h2>
<div class=big id=b${s}>--</div><div class=sub id=u${s}></div>
<div class=row><label>Rate</label><input type=range min=1 max=50 step=1 value=17 id=r${s}
 onpointerdown="editing['r${s}']=1" onchange="editing['r${s}']=0;send('${s}')"
 oninput="o${s}.value=this.value+' ml/min'"><output id=o${s}>17 ml/min</output></div>
<div class=row><label>Target</label><input type=number min=10 max=600 step=10 value=120 id=t${s}
 onfocus="editing['t${s}']=1" onchange="editing['t${s}']=0;send('${s}')"><span>ml</span></div>
<div><button class=go onclick="fetch('/run?side=${s}&on=1')">Start</button>
<button onclick="fetch('/run?side=${s}&on=0')">Stop</button>
<button class=warn onclick="fetch('/prime?side=${s}')">Prime</button>
<button onclick="fetch('/reset?side=${s}')">Reset run</button>
<button onclick="fetch('/refill?side=${s}')">Refilled</button></div></div>`}
cards.innerHTML=card('L')+card('R');
function send(s){fetch('/set?side='+s+'&rate='+document.getElementById('r'+s).value
 +'&target='+document.getElementById('t'+s).value)}
setInterval(async()=>{try{const j=await(await fetch('/status')).json();
for(const s of SIDES){const d=j[s];
document.getElementById('b'+s).textContent=
 d.run?d.eff.toFixed(0)+' ml/min':(d.done?'DONE':(d.low?'LOW RES':'stopped'));
document.getElementById('u'+s).textContent=
 d.del.toFixed(0)+' / '+d.tgt.toFixed(0)+' ml · '+Math.floor(d.el/60)+'m'+Math.floor(d.el%60)
 +'s · bag '+(d.lvl*100).toFixed(0)+'%';
if(!editing['r'+s]){document.getElementById('r'+s).value=d.rate;
 document.getElementById('o'+s).value=d.rate.toFixed(0)+' ml/min';}
if(!editing['t'+s])document.getElementById('t'+s).value=d.tgt;}}catch(e){}},1000);
</script></body></html>)HTML";

int sideArg() { return (server.arg("side") == "R") ? 1 : 0; }

void handleSet() {
  int s = sideArg();
  Side &S = sides[s];
  if (server.hasArg("rate"))
    S.rateReq = constrain(server.arg("rate").toFloat(), 1.0f, MAX_RATE);
  if (server.hasArg("target"))
    S.target = constrain(server.arg("target").toFloat(), 10.0f, MAX_TARGET);
  if (S.running) {  // live rate change, no kick (already moving)
    int duty = dutyForRate(s, S.rateReq, nullptr);
    if (!S.kickUntil) pumpWrite(s, duty);
    else S.kickTarget = duty;
  }
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
  if (S.running) {
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

void handleStatus() {
  char buf[360];
  int n = snprintf(buf, sizeof buf, "{");
  for (int s = 0; s < 2; s++) {
    Side &S = sides[s];
    float eff;
    dutyForRate(s, S.rateReq, &eff);
    if (S.running || S.priming) eff = S.actualDuty * ML_PER_MIN_AT_100 / 100.0f;
    n += snprintf(buf + n, sizeof buf - n,
                  "\"%c\":{\"run\":%d,\"prime\":%d,\"done\":%d,\"low\":%d,"
                  "\"rate\":%.1f,\"eff\":%.1f,\"tgt\":%.0f,\"del\":%.1f,"
                  "\"el\":%.0f,\"lvl\":%.3f}%s",
                  s == 0 ? 'L' : 'R', S.running, S.priming, S.done, S.lowStop,
                  S.rateReq, eff, S.target, S.delivered, S.elapsedS,
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
  Serial.println("\nSaline Pump Stage 6: gauges + dosing. Pumps start OFF.");
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
  Serial.printf("Stall floors: L=%d%% R=%d%%\n", sides[0].minPct,
                sides[1].minPct);

  SPI.begin(TFT_SCK, -1, TFT_MOSI, -1);
  tftL.begin(27000000);
  tftR.begin(27000000);
  drawFace(0);
  drawFace(1);

  WiFi.mode(WIFI_STA);
  WiFi.begin("PidgeonsNest", "3b5794e3e9");
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 15000) delay(250);
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi up, IP: ");
    Serial.println(WiFi.localIP());
  } else {
    WiFi.mode(WIFI_AP);
    WiFi.softAP("SalinePump-Test", "primefirst");
    Serial.print("Fallback AP up, IP: ");
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
      float flow = ML_PER_MIN_AT_100 * S.actualDuty / 100.0f * dtMin;
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

  // LED: solid while any pump runs, short heartbeat blink when idle
  bool anyRun = sides[0].running || sides[1].running || sides[0].priming ||
                sides[1].priming;
  digitalWrite(LED, anyRun ? HIGH : ((now % 1000) < 80 ? HIGH : LOW));

  ArduinoOTA.handle();
  server.handleClient();
}
