# ESP32 Smart Bin Firmware

Firmware for an ESP32-controlled multi-compartment smart dustbin. Opens the compartment matching the
AI-classified material category, keeps the rest locked, and auto-closes after disposal.

## Hardware (baseline build)

| Component | Qty | Notes |
|---|---|---|
| ESP32 DevKitC (or similar) | 1 | Wi-Fi + BLE capable |
| SG90 / MG996R servo motors | 1 per compartment (start with 5: plastic, glass, metal, paper, organic) | Drives the compartment flap lock |
| HX711 + load cell | 1 | Optional at launch; measured weight overrides the app's vision estimate |
| HC-SR04 ultrasonic sensor | 1 per compartment (optional) | Fill-level / "item deposited" confirmation |
| 5V/2A power supply | 1 | Servos draw more current than the ESP32's onboard regulator can supply — use a separate 5V rail |
| Status LED / buzzer | 1 | User feedback on open/lock events |

Wiring: servos on PWM-capable GPIOs (e.g. 13,14,27,26,25 for a 5-compartment build), HX711 DOUT/SCK on
two free GPIOs (e.g. 4,5), ultrasonic TRIG/ECHO per compartment as needed. Share ground between the ESP32
and the servo power rail.

## Flashing

1. Install [PlatformIO](https://platformio.org/) (VS Code extension) or Arduino IDE with the ESP32 board package.
2. Open `smart_bin/smart_bin.ino` (Arduino IDE) or the `smart_bin/` folder (PlatformIO).
3. Edit the `WIFI_SSID`, `WIFI_PASSWORD`, `BACKEND_HOST`, `DEVICE_UID`, and `SHARED_SECRET` constants at
   the top of the file — `SHARED_SECRET` must match `ESP32_SHARED_SECRET` in the backend's `.env`.
4. Select board "ESP32 Dev Module", select the correct serial port, and upload.
5. Open the Serial Monitor at 115200 baud to confirm it connects to Wi-Fi and starts sending status
   heartbeats (`POST /esp32/{device_uid}/status`) to the backend.
6. From the backend or app, trigger `POST /api/v1/esp32/{device_uid}/command` with
   `{"material_category": "plastic"}` to test a compartment opening manually before wiring it into the
   full scan flow.

## Protocol

- **Bin → backend** (heartbeat, every 30s): `POST /esp32/{device_uid}/status`, HMAC-SHA256 signed with
  `SHARED_SECRET` over the JSON body, signature in the `X-Signature` header. Registers the bin's current
  IP so the backend knows where to push commands.
- **Backend → bin** (command): `POST http://<bin-ip>/command` with `{"material_category": "...",
  "scan_id": "..."}`, also HMAC-signed. The bin verifies the signature before actuating anything.
- **BLE fallback**: for bins without Wi-Fi/router access, the same command JSON is written to a custom
  BLE characteristic by a phone acting as gateway (the app, when paired, relays the classification result
  over BLE instead of HTTP). See `ble_fallback.md` in this folder for the service/characteristic UUIDs.

## Extensibility

The firmware is organized around a `SensorModule` interface (`sensors.h`) so a load cell, ultrasonic
sensor, RFID reader, or camera module can be added independently without touching `smart_bin.ino`'s
core command-dispatch loop — implement `begin()`/`read()`/`name()` and register the module in `setup()`.

## Cloud polling mode (required when the backend is hosted)

The default firmware waits for the backend to POST a command to its local IP. That only works when the
backend runs on the same network. Once the backend is hosted (Render/Railway/etc.), your bin sits behind
a router with no public address and the cloud cannot reach it — so the bin must **ask** for commands
instead of waiting to be told.

Add this to `smart_bin.ino` and call `pollForCommand()` from `loop()` on a ~2 second interval:

```cpp
const unsigned long POLL_INTERVAL_MS = 2000;
unsigned long lastPoll = 0;

void pollForCommand() {
  if (WiFi.status() != WL_CONNECTED) return;

  // The backend signs {"device_uid": "..."} for this endpoint — keep the body shape identical.
  String signedBody = String("{\"device_uid\": \"") + DEVICE_UID + "\"}";
  String signature = hmacSha256Hex(SHARED_SECRET, signedBody);

  HTTPClient http;
  String url = String("https://") + BACKEND_HOST + "/api/v1/esp32/" + DEVICE_UID + "/pending-command";
  http.begin(url);
  http.addHeader("X-Signature", signature);
  int code = http.GET();

  if (code == 200) {
    StaticJsonDocument<256> doc;
    if (!deserializeJson(doc, http.getString()) && !doc["command"].isNull()) {
      String category = doc["command"]["material_category"].as<String>();
      int idx = findCompartment(category);
      if (idx >= 0) openCompartment(idx);
    }
  }
  http.end();
}
```

Then in `loop()`:

```cpp
if (millis() - lastPoll > POLL_INTERVAL_MS) {
  pollForCommand();
  lastPoll = millis();
}
```

Notes:
- Change `BACKEND_HOST` to your hosted domain (e.g. `your-backend.onrender.com`) and use `https://`.
  For HTTPS on ESP32 you'll need `WiFiClientSecure` — for a demo you can call `client.setInsecure()`,
  but for anything real, pin the certificate.
- The backend discards queued commands older than 2 minutes, so a bin that was offline won't suddenly
  open a compartment for a scan somebody did an hour ago.
- Polling every 2 seconds is fine for a handful of bins. If you deploy many bins, move to MQTT
  (see DEPLOYMENT.md §5, Option B) rather than scaling up polling.
