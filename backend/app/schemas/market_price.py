import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class MarketPriceOut(BaseModel):
    id: uuid.UUID
    category: str
    price_per_kg: Decimal
    currency: str
    updated_at: datetime
    source: str

    class Config:
        from_attributes = True


class MarketPriceUpdate(BaseModel):
    category: str
    price_per_kg: Decimal
    currency: str = "INR"
