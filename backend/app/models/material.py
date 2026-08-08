import enum
import uuid

from sqlalchemy import Column, String, Enum, Boolean, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class MaterialCategory(str, enum.Enum):
    PLASTIC = "plastic"
    GLASS = "glass"
    STEEL = "steel"
    ALUMINIUM = "aluminium"
    IRON = "iron"
    PAPER = "paper"
    CARDBOARD = "cardboard"
    ORGANIC = "organic"
    TEXTILE = "textile"
    EWASTE = "ewaste"


class PolymerType(str, enum.Enum):
    PET = "PET"
    HDPE = "HDPE"
    LDPE = "LDPE"
    PP = "PP"
    PS = "PS"
    PC = "PC"
    PVC = "PVC"
    ABS = "ABS"
    PLA = "PLA"


class Material(Base):
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, index=True, nullable=False)  # e.g. "PET", "GLASS", "PAPER"
    name = Column(String, nullable=False)
    category = Column(Enum(MaterialCategory), nullable=False)
    polymer_type = Column(Enum(PolymerType), nullable=True)  # only set for category == PLASTIC
    biodegradable = Column(Boolean, nullable=False, default=False)
    recyclable = Column(Boolean, nullable=False, default=True)
    reusable = Column(Boolean, nullable=False, default=False)
    description = Column(Text, nullable=True)
    disposal_instructions = Column(Text, nullable=True)
    recycling_instructions = Column(Text, nullable=True)
    base_price_per_kg = Column(Numeric(10, 2), nullable=False, default=0)

    co2_factor = relationship("CO2Factor", back_populates="material", uselist=False)
