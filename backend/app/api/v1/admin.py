from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.models.scan import Scan
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(require_roles(UserRole.ADMIN))):
    return db.query(User).all()


@router.get("/analytics/summary")
def analytics_summary(db: Session = Depends(get_db), _=Depends(require_roles(UserRole.ADMIN))):
    total_scans = db.query(Scan).count()
    total_users = db.query(User).count()
    return {
        "total_scans": total_scans,
        "total_users": total_users,
        # Extend with time-bucketed aggregates once analytics needs solidify (e.g. daily scan volume,
        # top materials by weight, CO2 saved trend) — keep as raw SQL/materialized views for perf at scale.
    }
