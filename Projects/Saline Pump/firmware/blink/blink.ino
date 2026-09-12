// Saline Pump — blink.ino: the 30-second "is this board alive?" test.
//
// Not part of the rig. This exists purely to split one question in two when
// the main firmware looks dead: is the BOARD/UPLOAD broken, or is my CODE
// broken? Flash this. If the LED blinks once a second and the serial monitor
// prints, the board and the upload path are fine and the fault is in
// gauges.ino. If this does nothing either, the fault is the board, the USB
// cable, the port or the IDE settings, and no amount of firmware will help.
//
// Board: ESP32 DevKitC 30-pin. Serial monitor at 115200.
// Safety: the two pump gates are driven LOW first, before anything else, so
// this sketch can never twitch a motor.

const int PUMP_L_GATE = 14;
const int PUMP_R_GATE = 13;
const int LED = 2;

void setup() {
  pinMode(PUMP_L_GATE, OUTPUT);
  digitalWrite(PUMP_L_GATE, LOW);
  pinMode(PUMP_R_GATE, OUTPUT);
  digitalWrite(PUMP_R_GATE, LOW);
  pinMode(LED, OUTPUT);

  Serial.begin(115200);
  delay(400);
  Serial.println();
  Serial.printf("BLINK TEST alive. Built %s %s\n", __DATE__, __TIME__);
  Serial.println("LED on GPIO2 should now flash once a second.");
}

void loop() {
  digitalWrite(LED, HIGH);
  delay(500);
  digitalWrite(LED, LOW);
  delay(500);
  Serial.printf("tick %lus\n", millis() / 1000);
}
