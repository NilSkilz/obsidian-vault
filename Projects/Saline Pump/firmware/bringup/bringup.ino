// Saline Pump v1 — Stage 4 bring-up sketch
//
// Job: hold both pump gates LOW from the first instant of setup(), then
// prove the ESP32 is alive (serial heartbeat + WiFi AP). No pump logic yet.
// Also runs ArduinoOTA so every flash after the first happens over WiFi:
// join the SalinePump-Test network, and the board shows up as a network
// port ("salinepump at 192.168.4.1") in Arduino IDE. OTA password: primefirst
//
// Flash the FIRST time over USB with the devkit BARE ON THE DESK, before it
// ever goes in the board socket. GPIO14 (Pump L gate) emits a PWM burst
// during boot; the 10k pulldown tames it and this sketch pins it off
// immediately after. GPIO13 (Pump R) is boot-clean but gets the same
// treatment.
//
// Board: ESP32 DevKitC 30-pin. Pin map per PCB v1 (locked 2026-08-20):
//   GPIO14 = Pump L gate   GPIO13 = Pump R gate   GPIO2 = onboard LED

#include <WiFi.h>
#include <ArduinoOTA.h>

const int PUMP_L_GATE = 14;
const int PUMP_R_GATE = 13;
const int LED = 2;

void setup() {
  // FIRST lines, before serial, before anything: gates off.
  pinMode(PUMP_L_GATE, OUTPUT);
  digitalWrite(PUMP_L_GATE, LOW);
  pinMode(PUMP_R_GATE, OUTPUT);
  digitalWrite(PUMP_R_GATE, LOW);

  pinMode(LED, OUTPUT);

  Serial.begin(115200);
  delay(300);
  Serial.println();
  Serial.println("Saline Pump bring-up. Pump gates GPIO14 + GPIO13 held LOW.");

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
  // every second, serial ping every 5s.
  static unsigned long lastBlink = 0;
  static unsigned long lastPrint = 0;
  unsigned long now = millis();

  digitalWrite(LED, (now - lastBlink) < 80 ? HIGH : LOW);
  if (now - lastBlink >= 1000) lastBlink = now;

  if (now - lastPrint > 5000) {
    lastPrint = now;
    Serial.println("alive, gates LOW");
  }

  ArduinoOTA.handle();
}
