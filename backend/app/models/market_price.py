import uuid

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String, nullable=False, index=True)  # plastic/glass/paper/metal/cardboard
    price_per_kg = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, nullable=False, default="INR")
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    source = Column(String, nullable=False, default="admin")  # admin | external_api
