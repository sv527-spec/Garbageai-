import enum
import uuid

from sqlalchemy import Column, String, ForeignKey, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class CollectionStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Collection(Base):
    """Supervisor-assigned collection run for a worker in an area."""

    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    area = Column(String, nullable=False)
    status = Column(Enum(CollectionStatus), nullable=False, default=CollectionStatus.ASSIGNED)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
