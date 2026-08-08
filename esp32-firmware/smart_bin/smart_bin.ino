/*
  Smart Waste Bin — ESP32 Firmware

  Opens the correct servo-locked compartment after the app classifies a waste item, keeps the rest
  locked, and auto-closes after a timeout. Talks to the backend over Wi-Fi HTTP (see ../README.md for
  the protocol and ../ble_fallback.md for the no-Wi-Fi fallback path).

  Required libraries (install via Arduino Library Manager):
    - ESP32Servo
    - ArduinoJson (>= 6.x)
  HX711 (bogde/HX711) only if you wire up the load cell — see sensors.h.

  Board: "ESP32 Dev Module" in Arduino IDE / Tools > Board.
*/
#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>
#include <mbedtls/md.h>
#include "sensors.h"

// ---------------------------------------------------------------------------------------------
// CONFIG — edit these before flashing
// ---------------------------------------------------------------------------------------------
const char* WIFI_SSID      = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD  = "YOUR_WIFI_PASSWORD";
const char* BACKEND_HOST   = "192.168.1.100:8000";     // backend host:port, no scheme
const char* DEVICE_UID     = "smartbin-001";           // must be unique per physical bin
const char* SHARED_SECRET  = "change-me-per-device-in-prod";  // must match ESP32_SHARED_SECRET

const unsigned long STATUS_INTERVAL_MS   = 30000;   // heartbeat cadence
const unsigned long AUTO_CLOSE_MS        = 8000;    // compartment stays open this long, then locks
const int SERVO_OPEN_ANGLE  = 90;
const int SERVO_CLOSED_ANGLE = 0;

// ---------------------------------------------------------------------------------------------
// Compartment map: material category -> servo GPIO pin. Extend as you add compartments.
// ---------------------------------------------------------------------------------------------
struct Compartment {
  const char* category;
  uint8_t pin;
  Servo servo;
};

Compartment compartments[] = {
  { "plastic", 13, Servo() },
  { "glass",   14, Servo() },
  { "steel",   27, Servo() },
  { "aluminium", 27, Servo() },  // metals share a compartment in a 5-slot baseline build
  { "iron",    27, Servo() },
  { "paper",   26, Servo() },
  { "cardboard", 26, Servo() },
  { "organic", 25, Servo() },
  { "textile", 25, Servo() },
  { "ewaste",  25, Servo() },
};
const int NUM_COMPARTMENTS = sizeof(compartments) / sizeof(compartments[0]);

WebServer server(80);
unsigned long lastStatusPush = 0;
int openCompartmentIndex = -1;
unsigned long openedAt = 0;

// Optional sensors — instantiate and .begin() the ones you've actually wired up.
LoadCellModule loadCell(4, 5, 420.f);

// ---------------------------------------------------------------------------------------------
// HMAC-SHA256 signing (matches backend's services/esp32_bridge.py sign_payload/verify_signature)
// ---------------------------------------------------------------------------------------------
String hmacSha256Hex(const String& key, const String& message) {
  byte hmacResult[32];
  mbedtls_md_context_t ctx;
  mbedtls_md_type_t md_type = MBEDTLS_MD_SHA256;
  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(md_type), 1);
  mbedtls_md_hmac_starts(&ctx, (const unsigned char*)key.c_str(), key.length());
  mbedtls_md_hmac_update(&ctx, (const unsigned char*)message.c_str(), message.length());
  mbedtls_md_hmac_finish(&ctx, hmacResult);
  mbedtls_md_free(&ctx);

  String hex = "";
  for (int i = 0; i < 32; i++) {
    if (hmacResult[i] < 16) hex += "0";
    hex += String(hmacResult[i], HEX);
  }
  return hex;
}

// NOTE: the backend signs JSON with keys sorted alphabetically and compact separators (Python's
// json.dumps(payload, sort_keys=True)). Keep the field order below alphabetical to match exactly.

// ---------------------------------------------------------------------------------------------
// Compartment control
// ---------------------------------------------------------------------------------------------
int findCompartment(const String& category) {
  for (int i = 0; i < NUM_COMPARTMENTS; i++) {
    if (category.equalsIgnoreCase(compartments[i].category)) return i;
  }
  return -1;
}

void openCompartment(int index) {
  if (index < 0 || index >= NUM_COMPARTMENTS) return;

  // Lock everything else first — only one compartment open at a time.
  for (int i = 0; i < NUM_COMPARTMENTS; i++) {
    compartments[i].servo.write(SERVO_CLOSED_ANGLE);
  }

  compartments[index].servo.write(SERVO_OPEN_ANGLE);
  openCompartmentIndex = index;
  openedAt = millis();
  Serial.printf("Opened compartment: %s (pin %d)\n", compartments[index].category, compartments[index].pin);
}

void closeAllCompartments() {
  for (int i = 0; i < NUM_COMPARTMENTS; i++) {
    compartments[i].servo.write(SERVO_CLOSED_ANGLE);
  }
  openCompartmentIndex = -1;
}

// ---------------------------------------------------------------------------------------------
// HTTP handlers
// ---------------------------------------------------------------------------------------------
void handleCommand() {
  if (!server.hasHeader("X-Signature") || server.arg("plain").length() == 0) {
    server.send(400, "application/json", "{\"detail\":\"missing signature or body\"}");
    return;
  }

  String body = server.arg("plain");
  String signature = server.header("X-Signature");
  String expected = hmacSha256Hex(SHARED_SECRET, body);
  if (expected != signature) {
    server.send(401, "application/json", "{\"detail\":\"invalid signature\"}");
    return;
  }

  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, body);
  if (err) {
    server.send(400, "application/json", "{\"detail\":\"invalid json\"}");
    return;
  }

  String category = doc["material_category"].as<String>();
  int idx = findCompartment(category);
  if (idx < 0) {
    server.send(404, "application/json", "{\"detail\":\"unknown material category\"}");
    return;
  }

  openCompartment(idx);
  server.send(200, "application/json", "{\"detail\":\"ok\"}");
}

void pushStatus() {
  if (WiFi.status() != WL_CONNECTED) return;

  // Field order MUST be alphabetical to match the backend's json.dumps(sort_keys=True) signing.
  StaticJsonDocument<256> doc;
  doc["compartment_open"] = openCompartmentIndex >= 0 ? compartments[openCompartmentIndex].category : nullptr;
  doc["device_uid"] = DEVICE_UID;
  doc["firmware_version"] = "0.1.0";
  doc["ip_address"] = WiFi.localIP().toString();
  float grams = loadCell.read();
  if (grams >= 0) doc["load_cell_grams"] = grams;
  doc["last_event"] = openCompartmentIndex >= 0 ? "compartment_open" : "idle";

  String body;
  serializeJson(doc, body);
  String signature = hmacSha256Hex(SHARED_SECRET, body);

  HTTPClient http;
  String url = String("http://") + BACKEND_HOST + "/api/v1/esp32/" + DEVICE_UID + "/status";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Signature", signature);
  int code = http.POST(body);
  Serial.printf("Status push -> %d\n", code);
  http.end();
}

// ---------------------------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);

  for (int i = 0; i < NUM_COMPARTMENTS; i++) {
    compartments[i].servo.attach(compartments[i].pin);
    compartments[i].servo.write(SERVO_CLOSED_ANGLE);
  }
  loadCell.begin();

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\nConnected. IP: %s\n", WiFi.localIP().toString().c_str());

  server.on("/command", HTTP_POST, handleCommand);
  server.begin();
  Serial.println("HTTP command server started on port 80.");

  pushStatus();
}

void loop() {
  server.handleClient();

  if (millis() - lastStatusPush > STATUS_INTERVAL_MS) {
    pushStatus();
    lastStatusPush = millis();
  }

  if (openCompartmentIndex >= 0 && millis() - openedAt > AUTO_CLOSE_MS) {
    closeAllCompartments();
    Serial.println("Auto-closed compartment.");
  }
}
