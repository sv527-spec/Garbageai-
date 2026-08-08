"""
Bridge between the backend and ESP32 smart bins.

Primary transport: Wi-Fi HTTP — the backend POSTs a command directly to the bin's local IP (bins
register their IP on each status heartbeat). BLE devices without direct internet access instead poll
`GET /esp32/{device_id}/pending-command` through a phone-as-gateway (see ESP32 firmware README).

Devices authenticate outbound requests to the backend (status/heartbeat) with an HMAC signature computed
from ESP32_SHARED_SECRET; the backend authenticates *to* devices the same way when pushing commands, so
neither side accepts spoofed traffic.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()


def sign_payload(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True).encode()
    return hmac.new(settings.esp32_shared_secret.encode(), body, hashlib.sha256).hexdigest()


def verify_signature(payload: dict[str, Any], signature: str) -> bool:
    expected = sign_payload(payload)
    return hmac.compare_digest(expected, signature)


async def push_command(device_ip: str, command: dict[str, Any]) -> bool:
    """Best-effort push to a bin over the local network. Returns False (never raises) on failure so a
    scan/dispose flow never breaks just because a bin is temporarily offline; the app still shows the
    classification result and the user can dispose manually."""
    signature = sign_payload(command)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(
                f"http://{device_ip}/command",
                json=command,
                headers={"X-Signature": signature},
            )
            return resp.status_code == 200
    except httpx.HTTPError:
        return False
