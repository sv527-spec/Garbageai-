import enum
import uuid

from sqlalchemy import Column, String, ForeignKey, DateTime, Numeric, Enum, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class WeightSource(str, enum.Enum):
    VISION_ESTIMATE = "vision"
    LOAD_CELL = "load_cell"
    MANUAL = "manual"


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    CLASSIFIED = "classified"
    DISPOSED = "disposed"
    REJECTED = "rejected"


class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=True)

    image_url = Column(String, nullable=True)
    confidence_score = Column(Numeric(5, 4), nullable=True)  # 0..1

    estimated_weight_kg = Column(Numeric(10, 4), nullable=True)
    weight_source = Column(Enum(WeightSource), nullable=False, default=WeightSource.VISION_ESTIMATE)
    weight_confidence = Column(Numeric(5, 4), nullable=True)

    co2_saved_kg = Column(Numeric(10, 4), nullable=True)
    earnings_estimate = Column(Numeric(10, 2), nullable=True)

    device_id = Column(UUID(as_uuid=True), ForeignKey("esp32_devices.id"), nullable=True)
    status = Column(Enum(ScanStatus), nullable=False, default=ScanStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
