# BLE Fallback Protocol

Used when the bin has no Wi-Fi/router access. The mobile app acts as a BLE-central gateway: it still
talks to the backend over the internet (via the phone's own connection) for classification, then relays
the resulting command to the bin over BLE instead of the bin talking to the backend directly.

- **Service UUID**: `6e400001-b5a3-f393-e0a9-e50e24dcca9e` (Nordic UART-style custom service)
- **Command characteristic (write)**: `6e400002-b5a3-f393-e0a9-e50e24dcca9e` — app writes the same JSON
  command payload used over HTTP: `{"material_category": "plastic", "scan_id": "..."}`.
- **Status characteristic (notify)**: `6e400003-b5a3-f393-e0a9-e50e24dcca9e` — bin notifies
  `{"compartment_open": "plastic", "event": "opened"}` / `"closed"` so the app can show live bin state.
- Pairing: bins advertise as `SmartBin-<device_uid>`; the app should let a supervisor/admin pair a bin to
  a location once during setup (stored in the `esp32_devices` table via `owner_id`/`location`).
