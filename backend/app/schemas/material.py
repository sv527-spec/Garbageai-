import uuid
from decimal import Decimal
from pydantic import BaseModel

from app.models.material import MaterialCategory, PolymerType


class MaterialOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    category: MaterialCategory
    polymer_type: PolymerType | None
    biodegradable: bool
    recyclable: bool
    reusable: bool
    description: str | None
    disposal_instructions: str | None
    recycling_instructions: str | None
    base_price_per_kg: Decimal

    class Config:
        from_attributes = True
