from math import radians, sin, cos, sqrt, atan2

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.recycling_center import RecyclingCenter
from app.models.user import UserRole
from app.schemas.recycling_center import RecyclingCenterOut, RecyclingCenterCreate

router = APIRouter()


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    R = 6371.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lng2 - lng1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


@router.get("", response_model=list[RecyclingCenterOut])
def list_recycling_centers(
    lat: float | None = Query(default=None),
    lng: float | None = Query(default=None),
    radius_km: float = Query(default=25),
    material: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(RecyclingCenter)
    if material:
        query = query.filter(RecyclingCenter.accepted_materials.contains([material.upper()]))
    centers = query.all()

    results = []
    for c in centers:
        distance = None
        if lat is not None and lng is not None:
            distance = round(_haversine_km(lat, lng, float(c.lat), float(c.lng)), 2)
            if distance > radius_km:
                continue
        out = RecyclingCenterOut.model_validate(c)
        out.distance_km = distance
        results.append(out)

    if lat is not None and lng is not None:
        results.sort(key=lambda r: (r.distance_km is None, r.distance_km))
    return results


@router.post("", response_model=RecyclingCenterOut, status_code=201)
def create_recycling_center(
    payload: RecyclingCenterCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN)),
):
    center = RecyclingCenter(**payload.model_dump())
    db.add(center)
    db.commit()
    db.refresh(center)
    return center
