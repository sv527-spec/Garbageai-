import uuid

from sqlalchemy import Column, String, Numeric, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class RecyclingCenter(Base):
    __tablename__ = "recycling_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    lat = Column(Numeric(9, 6), nullable=False)
    lng = Column(Numeric(9, 6), nullable=False)
    phone = Column(String, nullable=True)
    operating_hours = Column(JSONB, nullable=True)  # {"mon": "9:00-18:00", ...}
    accepted_materials = Column(ARRAY(String), nullable=False, default=list)  # material codes
    rating = Column(Numeric(3, 2), nullable=True)
    verified = Column(Boolean, nullable=False, default=False)
