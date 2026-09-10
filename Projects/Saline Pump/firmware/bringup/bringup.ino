// Saline Pump v1 — Stage 5 bring-up sketch (dry pump test)
//
// Adds pump control to the display/WiFi/OTA bring-up. The board now serves
// a phone-friendly test panel at http://salinepump.local (or its IP): a duty
// slider + Off/100%/Sweep per pump, an automated 0→100→0 sweep, and a big
// STOP ALL. Pump gates run LEDC PWM at 1kHz. Everything defaults OFF, and
// any manually set duty auto-stops after 30s so a forgotten browser tab
// can't leave a pump running. Screens show live duty per side. Starting a
// stopped pump below 90% fires a 250ms 100% kick-start to break roller
// stiction, then settles to the requested duty (so the sweep now shows where
// the pump HOLDS speed, not where it manages to start). Each pump has a
// "Set stall limit": drag the slider to where the pump just still holds, tap
// it, and that duty becomes a persistent (NVS) floor for nonzero commands.
//
// Stage 5 protocol (hardware.md): DRY, one pump at a time. Connect Pump L
// only, sweep it, feel that Q1 stays cold, pull the e-stop mid-run (pump
// dies, screens/ESP stay up), then repeat for R, then both together.
//
// Libraries: "Adafruit GC9A01A" + its deps (Adafruit GFX, Adafruit BusIO).
//
// WiFi: joins the house network (PidgeonsNest); falls back to its own AP
// (SalinePump-Test / primefirst) after 15s so OTA is never unreachable.
// OTA: network port "salinepump at <its IP>", password primefirst. An OTA
// update forces both pumps off before flashing. Serial only works over USB.
//
// Board: ESP32 DevKitC 30-pin. Pin map per PCB v1 (locked 2026-08-20):
//   GPIO14 = Pump L gate   GPIO13 = Pump R gate   GPIO2 = onboard LED
//   Displays (shared SPI): MOSI=23 SCK=18 DC=19 RST=15, CS L=5 / R=4
//   Display VCC + BLK to 3V3, never 5V.

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoOTA.h>
#include <Preferences.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_GC9A01A.h>

const int PUMP_L_GATE = 14;
const int PUMP_R_GATE = 13;
const int LED = 2;

const int TFT_MOSI = 23;
const int TFT_SCK = 18;
const int TFT_DC = 19;
const int TFT_RST = 15;  // shared reset line, both panels
const int TFT_CS_L = 5;
const int TFT_CS_R = 4;

const uint16_t COL_L = 0x07FF;  // cyan
const uint16_t COL_R = 0xFD20;  // orange
const uint16_t COL_DIM = 0x8410;

// 1kHz keeps MOSFET switching losses negligible (Q1/Q2 should stay cold);
// the mild motor hum at 1kHz is fine for a bench test.
const int PWM_FREQ = 1000;
const int PWM_RES = 8;  // duty 0-255
const unsigned long AUTO_STOP_MS = 30000;

// Kick-start: the peristaltic head's rollers need near-full torque to break
// away from standstill (bench test 2026-09-10: stalls below ~75% duty from
// rest, holds lower once moving). Starting a stopped pump below KICK_PCT_MAX
// gets a KICK_MS burst at 100%, then settles to the requested duty.
const int KICK_PCT_MAX = 90;
const unsigned long KICK_MS = 250;

// RST goes to the left object only: its begin() pulses the shared line and
// resets both panels, then the right begin() configures its panel without
// yanking reset again (which would wipe the left one's setup).
Adafruit_GC9A01A tftL(TFT_CS_L, TFT_DC, TFT_RST);
Adafruit_GC9A01A tftR(TFT_CS_R, TFT_DC, -1);

WebServer server(80);

int dutyPct[2] = {0, 0};  // 0 = L, 1 = R
unsigned long lastCmdMs = 0;

// Per-side kick-start state: 0 = no kick pending, else millis() deadline to
// drop from the 100% burst down to kickTarget.
unsigned long kickUntil[2] = {0, 0};
int kickTarget[2] = {0, 0};

// Per-side stall limit, found empirically with the slider: any nonzero duty
// command below it is clamped up to it. 0 = no limit set. Persisted in NVS
// so it survives reboots and OTA updates.
Preferences prefs;
int minPct[2] = {0, 0};

// Sweep state machine: -1 = idle, else the side being swept.
int sweepSide = -1;
int sweepPct = 0;
int sweepDir = 5;
unsigned long sweepLastMs = 0;

void pumpWrite(int side, int pct) {
  int pin = (side == 0) ? PUMP_L_GATE : PUMP_R_GATE;
  int duty = (255 * pct) / 100;
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin, duty);
#else
  ledcWrite(side, duty);  // channel number = side on the 2.x core
#endif
}

void drawCentred(Adafruit_GC9A01A &tft, const char *txt, int y, int size,
                 uint16_t colour) {
  int16_t x1, y1;
  uint16_t w, h;
  tft.setTextSize(size);
  tft.setTextColor(colour);
  tft.getTextBounds(txt, 0, 0, &x1, &y1, &w, &h);
  tft.setCursor(120 - w / 2, y - h / 2);
  tft.print(txt);
}

void drawDuty(int side) {
  Adafruit_GC9A01A &tft = (side == 0) ? tftL : tftR;
  uint16_t accent = (side == 0) ? COL_L : COL_R;
  tft.fillRect(30, 100, 180, 60, GC9A01A_BLACK);
  if (dutyPct[side] == 0) {
    drawCentred(tft, "OFF", 130, 5, COL_DIM);
  } else {
    char buf[8];
    snprintf(buf, sizeof buf, "%d%%", dutyPct[side]);
    drawCentred(tft, buf, 130, 5, accent);
  }
}

void drawFace(Adafruit_GC9A01A &tft, const char *label, uint16_t accent) {
  tft.fillScreen(GC9A01A_BLACK);
  for (int r = 112; r <= 116; r++) tft.drawCircle(120, 120, r, accent);
  drawCentred(tft, label, 58, 4, GC9A01A_WHITE);
  drawCentred(tft, "DRY TEST", 180, 2, COL_DIM);
}

void heartbeatDot(bool on) {
  tftL.fillCircle(120, 208, 4, on ? COL_L : GC9A01A_BLACK);
  tftR.fillCircle(120, 208, 4, on ? COL_R : GC9A01A_BLACK);
}

void setDuty(int side, int pct) {
  pct = constrain(pct, 0, 100);
  if (pct > 0 && pct < minPct[side]) pct = minPct[side];  // stall limit
  bool kick = (dutyPct[side] == 0 && pct > 0 && pct < KICK_PCT_MAX);
  if (kick) {
    pumpWrite(side, 100);
    kickUntil[side] = millis() + KICK_MS;
    kickTarget[side] = pct;
  } else if (kickUntil[side] && pct > 0) {
    kickTarget[side] = pct;  // slider moved mid-kick: keep the burst going
  } else {
    kickUntil[side] = 0;  // Off (or a high duty) cancels a pending kick
    pumpWrite(side, pct);
  }
  if (pct != dutyPct[side]) {
    dutyPct[side] = pct;
    drawDuty(side);
  }
  lastCmdMs = millis();
  Serial.printf("Pump %c -> %d%%%s\n", side == 0 ? 'L' : 'R', pct,
                kick ? " (kick-start)" : "");
}

void stopAll() {
  sweepSide = -1;
  setDuty(0, 0);
  setDuty(1, 0);
}

const char PAGE[] PROGMEM = R"HTML(<!doctype html><html><head>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Saline Pump dry test</title><style>
body{background:#111;color:#eee;font-family:-apple-system,sans-serif;margin:16px;text-align:center}
h1{font-size:1.15em;color:#aaa}
.pump{border:1px solid #333;border-radius:14px;padding:10px;margin:12px 0}
.pump h2{margin:4px 0}
button{font-size:1.05em;padding:12px 14px;margin:3px;border:0;border-radius:10px;background:#333;color:#eee}
.L h2,#vL{color:#0ff}.R h2,#vR{color:#f90}
.stop{background:#a00;color:#fff;font-size:1.3em;width:100%;padding:16px;margin-top:8px}
.val{font-size:2em;font-weight:700;margin:6px}
input[type=range]{width:95%;height:34px;margin:4px 0}
.lim{color:#888;display:block;margin-top:2px}
small{color:#888}
</style></head><body>
<h1>Saline Pump &mdash; Stage 5 dry test</h1>
<div class="pump L"><h2>Pump L</h2><div class=val id=vL>OFF</div>
<input type=range min=0 max=100 step=1 value=0 id=sL oninput="slide('L')">
<div><button onclick="set('L',0)">Off</button><button onclick="set('L',100)">100%</button>
<button onclick="sweep('L')">Sweep</button><button onclick="setMin('L')">Set stall limit</button></div>
<small class=lim id=mL>stall limit: none</small></div>
<div class="pump R"><h2>Pump R</h2><div class=val id=vR>OFF</div>
<input type=range min=0 max=100 step=1 value=0 id=sR oninput="slide('R')">
<div><button onclick="set('R',0)">Off</button><button onclick="set('R',100)">100%</button>
<button onclick="sweep('R')">Sweep</button><button onclick="setMin('R')">Set stall limit</button></div>
<small class=lim id=mR>stall limit: none</small></div>
<button class=stop onclick="fetch('/stop')">STOP ALL</button>
<p><small>Dry only, one pump at a time. Manual duty auto-stops after 30s.
Pull the e-stop mid-run: pump dies, this page and the screens stay up.<br>
Stall hunt: start high, drag the slider down until the pump stalls, nudge back
up one step to where it just holds, tap Set stall limit. The board then never
runs that pump below the limit. To clear a limit: slider to 0, tap Set stall limit.</small></p>
<script>
const T={};
function set(s,p){fetch('/set?side='+s+'&pct='+p)}
function sweep(s){fetch('/sweep?side='+s)}
function slide(s){clearTimeout(T[s]);const v=document.getElementById('s'+s).value;
T[s]=setTimeout(()=>set(s,v),120)}
function setMin(s){const v=document.getElementById('s'+s).value;
fetch('/min?side='+s+'&pct='+v)}
setInterval(async()=>{try{const j=await(await fetch('/status')).json();
vL.textContent=j.L?j.L+'%':'OFF';vR.textContent=j.R?j.R+'%':'OFF';
mL.textContent='stall limit: '+(j.minL?j.minL+'%':'none');
mR.textContent='stall limit: '+(j.minR?j.minR+'%':'none');
}catch(e){}},1000);
</script></body></html>)HTML";

void handleSet() {
  int side = (server.arg("side") == "R") ? 1 : 0;
  sweepSide = -1;  // a manual command cancels any running sweep
  setDuty(side, server.arg("pct").toInt());
  server.send(200, "text/plain", "ok");
}

void handleSweep() {
  int side = (server.arg("side") == "R") ? 1 : 0;
  setDuty(1 - side, 0);  // one pump at a time
  sweepSide = side;
  sweepPct = 0;
  sweepDir = 5;
  sweepLastMs = millis();
  Serial.printf("Sweep started on pump %c\n", side == 0 ? 'L' : 'R');
  server.send(200, "text/plain", "ok");
}

void handleMin() {
  int side = (server.arg("side") == "R") ? 1 : 0;
  int pct = constrain(server.arg("pct").toInt(), 0, 100);
  minPct[side] = pct;
  prefs.putInt(side == 0 ? "minL" : "minR", pct);
  Serial.printf("Pump %c stall limit -> %d%%\n", side == 0 ? 'L' : 'R', pct);
  server.send(200, "text/plain", "ok");
}

void handleStatus() {
  char buf[80];
  snprintf(buf, sizeof buf,
           "{\"L\":%d,\"R\":%d,\"minL\":%d,\"minR\":%d,\"sweep\":%d}",
           dutyPct[0], dutyPct[1], minPct[0], minPct[1], sweepSide);
  server.send(200, "application/json", buf);
}

void setup() {
  // FIRST lines, before serial, before anything: gates off.
  pinMode(PUMP_L_GATE, OUTPUT);
  digitalWrite(PUMP_L_GATE, LOW);
  pinMode(PUMP_R_GATE, OUTPUT);
  digitalWrite(PUMP_R_GATE, LOW);

  // Park both chip-selects high before either display is touched, so the
  // idle screen can't eavesdrop on the other one's init commands.
  pinMode(TFT_CS_L, OUTPUT);
  digitalWrite(TFT_CS_L, HIGH);
  pinMode(TFT_CS_R, OUTPUT);
  digitalWrite(TFT_CS_R, HIGH);

  pinMode(LED, OUTPUT);

  Serial.begin(115200);
  delay(300);
  Serial.println();
  Serial.println("Saline Pump bring-up, Stage 5. Pumps start OFF.");

  // Hand the gate pins to LEDC at duty 0. The pulldowns cover the gap
  // between reset and this point.
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

  // Stall limits from NVS (set from the test panel, 0 = none).
  prefs.begin("pump", false);
  minPct[0] = prefs.getInt("minL", 0);
  minPct[1] = prefs.getInt("minR", 0);
  Serial.printf("Stall limits: L=%d%% R=%d%%\n", minPct[0], minPct[1]);

  // Claim the SPI bus with our pins (no MISO — displays are write-only,
  // and GPIO19 is busy being DC). The library's own begin() is then a no-op.
  SPI.begin(TFT_SCK, -1, TFT_MOSI, -1);
  tftL.begin(27000000);  // 27MHz; drop to 10000000 if a screen shows garbage
  tftR.begin(27000000);
  drawFace(tftL, "L", COL_L);
  drawFace(tftR, "R", COL_R);
  drawDuty(0);
  drawDuty(1);
  Serial.println("Displays up: L=cyan on CS5, R=orange on CS4");

  // Join the house WiFi. Fall back to our own AP if it doesn't take, so
  // the board is never OTA-unreachable over a typo or a router sulk.
  WiFi.mode(WIFI_STA);
  WiFi.begin("PidgeonsNest", "3b5794e3e9");
  Serial.print("Joining PidgeonsNest");
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 15000) {
    delay(250);
    Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi up on PidgeonsNest, IP: ");
    Serial.println(WiFi.localIP());
  } else {
    WiFi.mode(WIFI_AP);
    WiFi.softAP("SalinePump-Test", "primefirst");
    Serial.print("House WiFi failed, fallback AP SalinePump-Test up, IP: ");
    Serial.println(WiFi.softAPIP());
  }

  // OTA. An update reboots the chip, and the pulldowns hold the gates
  // through the reboot, so mid-flash the pumps stay off.
  ArduinoOTA.setHostname("salinepump");
  ArduinoOTA.setPassword("primefirst");
  ArduinoOTA.onStart([]() {
    stopAll();
    Serial.println("OTA update starting, pumps forced off");
  });
  ArduinoOTA.onEnd([]() { Serial.println("OTA done, rebooting"); });
  ArduinoOTA.onError([](ota_error_t err) {
    Serial.printf("OTA error %u\n", err);
  });
  ArduinoOTA.begin();

  server.on("/", []() { server.send_P(200, "text/html", PAGE); });
  server.on("/set", handleSet);
  server.on("/sweep", handleSweep);
  server.on("/min", handleMin);
  server.on("/stop", []() {
    stopAll();
    server.send(200, "text/plain", "stopped");
  });
  server.on("/status", handleStatus);
  server.begin();

  Serial.print("Test panel: http://salinepump.local/ or http://");
  Serial.println(WiFi.status() == WL_CONNECTED ? WiFi.localIP()
                                               : WiFi.softAPIP());
}

void loop() {
  unsigned long now = millis();

  // Kick-start settle: drop from the 100% burst to the requested duty.
  for (int s = 0; s < 2; s++) {
    if (kickUntil[s] && now >= kickUntil[s]) {
      kickUntil[s] = 0;
      pumpWrite(s, kickTarget[s]);
    }
  }

  // Non-blocking heartbeat: short blink every second (LED + a dot on each
  // screen), serial ping every 5s.
  static unsigned long lastBlink = 0;
  static unsigned long lastPrint = 0;
  static bool dotOn = false;

  bool on = (now - lastBlink) < 80;
  digitalWrite(LED, on ? HIGH : LOW);
  if (on != dotOn) {
    dotOn = on;
    heartbeatDot(on);
  }
  if (now - lastBlink >= 1000) lastBlink = now;

  if (now - lastPrint > 5000) {
    lastPrint = now;
    Serial.printf("alive, L=%d%% R=%d%%\n", dutyPct[0], dutyPct[1]);
  }

  // Sweep: 5% step every 500ms, 0 -> 100 -> 0, ~20s total, ends OFF.
  if (sweepSide >= 0 && now - sweepLastMs >= 500) {
    sweepLastMs = now;
    sweepPct += sweepDir;
    if (sweepPct >= 100) {
      sweepPct = 100;
      sweepDir = -5;
    }
    setDuty(sweepSide, sweepPct);
    if (sweepPct <= 0) {
      Serial.println("Sweep done");
      sweepSide = -1;
    }
  }

  // Dead-man: a manually set duty with no fresh command for 30s stops
  // everything. Sweep steps count as commands, so sweeps never trip it.
  if ((dutyPct[0] > 0 || dutyPct[1] > 0) && sweepSide < 0 &&
      now - lastCmdMs > AUTO_STOP_MS) {
    Serial.println("Auto-stop: no command for 30s");
    stopAll();
  }

  ArduinoOTA.handle();
  server.handleClient();
}
