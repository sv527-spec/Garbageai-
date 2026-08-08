import uuid
from decimal import Decimal
from pydantic import BaseModel

from app.models.leaderboard import LeaderboardPeriod


class LeaderboardEntryOut(BaseModel):
    user_id: uuid.UUID
    full_name: str
    period: LeaderboardPeriod
    district: str | None
    state: str | None
    total_weight_kg: Decimal
    total_co2_kg: Decimal
    total_earnings: Decimal
    streak_days: int
    rank: int | None

    class Config:
        from_attributes = True
