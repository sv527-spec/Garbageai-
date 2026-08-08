import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel

from app.models.scan import WeightSource, ScanStatus
from app.schemas.material import MaterialOut


class ScanCreateResponse(BaseModel):
    """What the client gets back immediately after uploading a scan image."""

    id: uuid.UUID
    material: MaterialOut | None
    confidence_score: Decimal | None
    estimated_weight_kg: Decimal | None
    weight_source: WeightSource
    weight_confidence: Decimal | None
    co2_saved_kg: Decimal | None
    tree_equivalent: Decimal | None
    energy_saved_kwh: Decimal | None
    landfill_volume_reduced_l: Decimal | None
    earnings_estimate: Decimal | None
    status: ScanStatus
    created_at: datetime
    calculation_notes: dict

    class Config:
        from_attributes = True


class ScanOut(BaseModel):
    id: uuid.UUID
    material: MaterialOut | None
    confidence_score: Decimal | None
    estimated_weight_kg: Decimal | None
    co2_saved_kg: Decimal | None
    earnings_estimate: Decimal | None
    status: ScanStatus
    created_at: datetime

    class Config:
        from_attributes = True
