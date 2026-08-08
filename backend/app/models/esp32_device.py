import uuid

from sqlalchemy import Column, String, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ESP32Device(Base):
    __tablename__ = "esp32_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_uid = Column(String, unique=True, nullable=False)  # burned-in chip ID
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # supervisor/admin
    location = Column(String, nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    firmware_version = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)

    # --- Cloud polling mode ---------------------------------------------------------------
    # When the backend is hosted in the cloud, it cannot reach a bin sitting behind a home/campus
    # router (NAT). Instead of pushing to the bin's local IP, the command is queued here and the bin
    # picks it up on its next poll of GET /esp32/{device_uid}/pending-command.
    # Only one command is held at a time — a newer command supersedes an unclaimed older one, which is
    # the behaviour we want (the latest scan is the one the user is standing in front of).
    pending_category = Column(String, nullable=True)
    pending_scan_id = Column(String, nullable=True)
    pending_created_at = Column(DateTime(timezone=True), nullable=True)
