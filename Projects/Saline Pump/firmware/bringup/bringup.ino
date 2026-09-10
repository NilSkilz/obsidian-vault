// Saline Pump v1 — Stage 4/6 bring-up sketch
//
// Job: hold both pump gates LOW from the first instant of setup(), then
// prove the ESP32 is alive (serial heartbeat + WiFi AP + OTA), and now
// drive the two round GC9A01 gauges: left shows a cyan L, right an orange
// R, each with a READY tag and a heartbeat dot that blinks with the LED.
// If the letters come up on the wrong sides, the CS wires are swapped.
//
// Needs library: "Adafruit GC9A01A" (Library Manager; say yes to
// installing its dependencies, Adafruit GFX + BusIO).
//
// OTA: join the SalinePump-Test network (password primefirst) and the
// board appears as network port "salinepump at 192.168.4.1" in the IDE.
// OTA password: primefirst. Serial only works over USB.
//
// Board: ESP32 DevKitC 30-pin. Pin map per PCB v1 (locked 2026-08-20):
//   GPIO14 = Pump L gate   GPIO13 = Pump R gate   GPIO2 = onboard LED
//   Displays (shared SPI): MOSI=23 SCK=18 DC=19 RST=15, CS L=5 / R=4
//   Display VCC + BLK to 3V3, never 5V.

#include <WiFi.h>
#include <ArduinoOTA.h>
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

// RST goes to the left object only: its begin() pulses the shared line and
// resets both panels, then the right begin() configures its panel without
// yanking reset again (which would wipe the left one's setup).
Adafruit_GC9A01A tftL(TFT_CS_L, TFT_DC, TFT_RST);
Adafruit_GC9A01A tftR(TFT_CS_R, TFT_DC, -1);

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

void drawFace(Adafruit_GC9A01A &tft, const char *label, uint16_t accent) {
  tft.fillScreen(GC9A01A_BLACK);
  for (int r = 112; r <= 116; r++) tft.drawCircle(120, 120, r, accent);
  drawCentred(tft, label, 90, 7, GC9A01A_WHITE);
  drawCentred(tft, "READY", 150, 2, accent);
  drawCentred(tft, "gates LOW", 204, 1, 0x8410);
}

void heartbeatDot(bool on) {
  tftL.fillCircle(120, 180, 4, on ? COL_L : GC9A01A_BLACK);
  tftR.fillCircle(120, 180, 4, on ? COL_R : GC9A01A_BLACK);
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
  Serial.println("Saline Pump bring-up. Pump gates GPIO14 + GPIO13 held LOW.");

  // Claim the SPI bus with our pins (no MISO — displays are write-only,
  // and GPIO19 is busy being DC). The library's own begin() is then a no-op.
  SPI.begin(TFT_SCK, -1, TFT_MOSI, -1);
  tftL.begin(27000000);  // 27MHz; drop to 10000000 if a screen shows garbage
  tftR.begin(27000000);
  drawFace(tftL, "L", COL_L);
  drawFace(tftR, "R", COL_R);
  Serial.println("Displays up: L=cyan on CS5, R=orange on CS4");

  WiFi.softAP("SalinePump-Test", "primefirst");
  Serial.print("WiFi AP up: SalinePump-Test  password: primefirst  IP: ");
  Serial.println(WiFi.softAPIP());

  // OTA. An update reboots the chip, and the pulldowns hold the gates
  // through the reboot, so mid-flash the pumps stay off.
  ArduinoOTA.setHostname("salinepump");
  ArduinoOTA.setPassword("primefirst");
  ArduinoOTA.onStart([]() {
    // Gates are already LOW, but make it explicit before flash writes begin.
    digitalWrite(PUMP_L_GATE, LOW);
    digitalWrite(PUMP_R_GATE, LOW);
    Serial.println("OTA update starting, gates LOW");
  });
  ArduinoOTA.onEnd([]() { Serial.println("OTA done, rebooting"); });
  ArduinoOTA.onError([](ota_error_t err) {
    Serial.printf("OTA error %u\n", err);
  });
  ArduinoOTA.begin();
  Serial.println("OTA ready: hostname salinepump, IP 192.168.4.1");
}

void loop() {
  // Non-blocking heartbeat so OTA gets serviced constantly: short blink
  // every second (LED + a dot on each screen), serial ping every 5s.
  static unsigned long lastBlink = 0;
  static unsigned long lastPrint = 0;
  static bool dotOn = false;
  unsigned long now = millis();

  bool on = (now - lastBlink) < 80;
  digitalWrite(LED, on ? HIGH : LOW);
  if (on != dotOn) {
    dotOn = on;
    heartbeatDot(on);
  }
  if (now - lastBlink >= 1000) lastBlink = now;

  if (now - lastPrint > 5000) {
    lastPrint = now;
    Serial.println("alive, gates LOW");
  }

  ArduinoOTA.handle();
}
