import enum
import uuid

from sqlalchemy import Column, String, ForeignKey, Numeric, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class LeaderboardPeriod(str, enum.Enum):
    DAILY = "daily"
    MONTHLY = "monthly"
    ALLTIME = "alltime"


class LeaderboardEntry(Base):
    """Rollup table, recomputed periodically (see services/leaderboard_rollup.py, run via cron/worker)."""

    __tablename__ = "leaderboard_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    period = Column(Enum(LeaderboardPeriod), nullable=False)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)

    total_weight_kg = Column(Numeric(12, 4), nullable=False, default=0)
    total_co2_kg = Column(Numeric(12, 4), nullable=False, default=0)
    total_earnings = Column(Numeric(12, 2), nullable=False, default=0)
    streak_days = Column(Integer, nullable=False, default=0)
    rank = Column(Integer, nullable=True)

    user = relationship("User")
