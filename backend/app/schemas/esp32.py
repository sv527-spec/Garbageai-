import uuid
from pydantic import BaseModel


class ESP32Command(BaseModel):
    """Sent to a bin after classification: tells it which compartment to unlock."""

    material_category: str  # e.g. "plastic", "glass", "metal", "paper", "organic"
    scan_id: uuid.UUID | None = None


class ESP32Status(BaseModel):
    """Heartbeat/status payload posted by the ESP32 itself."""

    device_uid: str
    firmware_version: str | None = None
    ip_address: str | None = None
    load_cell_grams: float | None = None
    compartment_open: str | None = None
    last_event: str | None = None
