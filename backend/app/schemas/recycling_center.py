import uuid
from decimal import Decimal
from pydantic import BaseModel


class RecyclingCenterOut(BaseModel):
    id: uuid.UUID
    name: str
    address: str
    lat: Decimal
    lng: Decimal
    phone: str | None
    operating_hours: dict | None
    accepted_materials: list[str]
    rating: Decimal | None
    verified: bool
    distance_km: float | None = None

    class Config:
        from_attributes = True


class RecyclingCenterCreate(BaseModel):
    name: str
    address: str
    lat: Decimal
    lng: Decimal
    phone: str | None = None
    operating_hours: dict | None = None
    accepted_materials: list[str] = []
