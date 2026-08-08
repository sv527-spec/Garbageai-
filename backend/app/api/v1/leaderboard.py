from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.leaderboard import LeaderboardEntry, LeaderboardPeriod
from app.schemas.leaderboard import LeaderboardEntryOut

router = APIRouter()


@router.get("", response_model=list[LeaderboardEntryOut])
def get_leaderboard(
    period: LeaderboardPeriod = Query(default=LeaderboardPeriod.MONTHLY),
    scope: str = Query(default="national", pattern="^(district|state|national)$"),
    district: str | None = Query(default=None),
    state: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(LeaderboardEntry).options(joinedload(LeaderboardEntry.user)).filter(
        LeaderboardEntry.period == period
    )
    if scope == "district" and district:
        query = query.filter(LeaderboardEntry.district == district)
    elif scope == "state" and state:
        query = query.filter(LeaderboardEntry.state == state)

    entries = query.order_by(LeaderboardEntry.rank.asc().nulls_last()).limit(limit).all()
    return [
        LeaderboardEntryOut(
            user_id=e.user_id,
            full_name=e.user.full_name,
            period=e.period,
            district=e.district,
            state=e.state,
            total_weight_kg=e.total_weight_kg,
            total_co2_kg=e.total_co2_kg,
            total_earnings=e.total_earnings,
            streak_days=e.streak_days,
            rank=e.rank,
        )
        for e in entries
    ]
