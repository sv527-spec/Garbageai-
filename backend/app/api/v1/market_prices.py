from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles, get_current_user
from app.models.market_price import MarketPrice
from app.models.user import User, UserRole
from app.schemas.market_price import MarketPriceOut, MarketPriceUpdate

router = APIRouter()


@router.get("", response_model=list[MarketPriceOut])
def list_market_prices(db: Session = Depends(get_db)):
    return db.query(MarketPrice).order_by(MarketPrice.category).all()


@router.put("", response_model=MarketPriceOut)
def upsert_market_price(
    payload: MarketPriceUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    row = db.query(MarketPrice).filter(MarketPrice.category == payload.category).first()
    if row:
        row.price_per_kg = payload.price_per_kg
        row.currency = payload.currency
        row.updated_by = admin.id
        row.source = "admin"
    else:
        row = MarketPrice(
            category=payload.category,
            price_per_kg=payload.price_per_kg,
            currency=payload.currency,
            updated_by=admin.id,
            source="admin",
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row
