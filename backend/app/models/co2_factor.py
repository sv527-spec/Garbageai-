import uuid

from sqlalchemy import Column, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CO2Factor(Base):
    """Emission/impact factors per kg of a material. Admin-editable, source-cited for transparency."""

    __tablename__ = "co2_factors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False, unique=True)

    co2_saved_recycle_per_kg = Column(Numeric(10, 4), nullable=False, default=0)  # kg CO2e
    co2_saved_reuse_per_kg = Column(Numeric(10, 4), nullable=False, default=0)  # kg CO2e
    energy_saved_per_kg_kwh = Column(Numeric(10, 4), nullable=False, default=0)
    landfill_volume_reduced_per_kg_l = Column(Numeric(10, 4), nullable=False, default=0)
    tree_equivalent_per_kg = Column(Numeric(10, 6), nullable=False, default=0)  # trees/year equivalent
    source_note = Column(Text, nullable=True)  # citation, e.g. "US EPA WARM model v15"

    material = relationship("Material", back_populates="co2_factor")
