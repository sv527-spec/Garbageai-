from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.esp32_device import ESP32Device
from app.schemas.esp32 import ESP32Command, ESP32Status
from app.services.esp32_bridge import verify_signature, push_command

router = APIRouter()

# A queued command older than this is stale — the user has walked away. Discard rather than serve it.
PENDING_COMMAND_TTL_SECONDS = 120


@router.post("/{device_uid}/status")
def post_status(
    device_uid: str,
    payload: ESP32Status,
    x_signature: str = Header(...),
    db: Session = Depends(get_db),
):
    """Heartbeat endpoint the ESP32 firmware calls periodically. Registers/updates the device."""
    if not verify_signature(payload.model_dump(), x_signature):
        raise HTTPException(status_code=401, detail="Invalid device signature")

    device = db.query(ESP32Device).filter(ESP32Device.device_uid == device_uid).first()
    if not device:
        device = ESP32Device(device_uid=device_uid)
        db.add(device)

    device.firmware_version = payload.firmware_version
    device.ip_address = payload.ip_address
    device.last_seen = datetime.now(timezone.utc)
    db.commit()
    return {"detail": "ok"}


@router.post("/{device_uid}/command")
async def send_command(
    device_uid: str,
    payload: ESP32Command,
    mode: str = "auto",  # "auto" | "push" | "queue"
    db: Session = Depends(get_db),
):
    """Trigger a compartment open on a bin.

    Two delivery modes, because they suit different deployments:

    - **push**: backend POSTs directly to the bin's local IP. Low latency, but only works when the
      backend and the bin are on the same network (i.e. local development).
    - **queue**: command is stored and the bin collects it on its next poll. Required when the backend
      is hosted in the cloud, since a bin behind NAT has no reachable address.

    `auto` (the default) tries a direct push and falls back to queueing, so the same call works in both
    local and hosted deployments without the caller needing to know which.
    """
    device = db.query(ESP32Device).filter(ESP32Device.device_uid == device_uid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not registered")

    if mode in ("auto", "push") and device.ip_address:
        if await push_command(device.ip_address, payload.model_dump(mode="json")):
            return {"detail": "command pushed", "delivery": "push"}
        if mode == "push":
            raise HTTPException(status_code=502, detail="Device did not acknowledge the command")

    device.pending_category = payload.material_category
    device.pending_scan_id = str(payload.scan_id) if payload.scan_id else None
    device.pending_created_at = datetime.now(timezone.utc)
    db.commit()
    return {"detail": "command queued for next device poll", "delivery": "queue"}


@router.get("/{device_uid}/pending-command")
def get_pending_command(
    device_uid: str,
    x_signature: str = Header(...),
    db: Session = Depends(get_db),
):
    """Polled by the bin every few seconds when it can't be reached directly (cloud-hosted backend).

    Returns at most one command and clears it in the same transaction, so a command is delivered once.
    Commands older than PENDING_COMMAND_TTL_SECONDS are discarded rather than served — otherwise a bin
    that was offline would pop open a compartment for a scan someone did an hour ago.
    """
    if not verify_signature({"device_uid": device_uid}, x_signature):
        raise HTTPException(status_code=401, detail="Invalid device signature")

    device = db.query(ESP32Device).filter(ESP32Device.device_uid == device_uid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not registered")

    device.last_seen = datetime.now(timezone.utc)

    if not device.pending_category or not device.pending_created_at:
        db.commit()
        return {"command": None}

    age = (datetime.now(timezone.utc) - device.pending_created_at).total_seconds()
    category, scan_id = device.pending_category, device.pending_scan_id

    # Clear it either way — served or expired, it should not be handed out again.
    device.pending_category = None
    device.pending_scan_id = None
    device.pending_created_at = None
    db.commit()

    if age > PENDING_COMMAND_TTL_SECONDS:
        return {"command": None, "detail": "expired"}

    return {"command": {"material_category": category, "scan_id": scan_id}}
