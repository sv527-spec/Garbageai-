"""
Recomputes leaderboard_entries from raw scan data. Intended to run on a schedule (cron / Celery beat /
a simple `docker compose run backend python -m app.services.leaderboard_rollup`) rather than per-request,
since it aggregates across all users.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.scan import Scan
from app.models.user import User
from app.models.leaderboard import LeaderboardEntry, LeaderboardPeriod


def _period_start(period: LeaderboardPeriod) -> datetime | None:
    now = datetime.now(timezone.utc)
    if period == LeaderboardPeriod.DAILY:
        return now - timedelta(days=1)
    if period == LeaderboardPeriod.MONTHLY:
        return now - timedelta(days=30)
    return None  # ALLTIME


def rollup(db: Session, period: LeaderboardPeriod) -> None:
    query = (
        db.query(
            Scan.user_id,
            func.sum(Scan.estimated_weight_kg).label("weight"),
            func.sum(Scan.co2_saved_kg).label("co2"),
            func.sum(Scan.earnings_estimate).label("earnings"),
        )
        .group_by(Scan.user_id)
    )
    start = _period_start(period)
    if start:
        query = query.filter(Scan.created_at >= start)

    rows = query.all()
    ranked = sorted(rows, key=lambda r: (r.weight or 0), reverse=True)

    db.query(LeaderboardEntry).filter(LeaderboardEntry.period == period).delete()
    for idx, row in enumerate(ranked, start=1):
        user = db.query(User).filter(User.id == row.user_id).first()
        db.add(
            LeaderboardEntry(
                user_id=row.user_id,
                period=period,
                district=user.district if user else None,
                state=user.state if user else None,
                total_weight_kg=row.weight or 0,
                total_co2_kg=row.co2 or 0,
                total_earnings=row.earnings or 0,
                streak_days=0,  # TODO: compute from consecutive scan-day gaps once needed
                rank=idx,
            )
        )
    db.commit()


def run_all() -> None:
    db = SessionLocal()
    try:
        for period in LeaderboardPeriod:
            rollup(db, period)
    finally:
        db.close()


if __name__ == "__main__":
    run_all()
