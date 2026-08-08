from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.material import Material
from app.schemas.material import MaterialOut

router = APIRouter()


@router.get("", response_model=list[MaterialOut])
def list_materials(db: Session = Depends(get_db)):
    return db.query(Material).all()


@router.get("/{code}", response_model=MaterialOut)
def get_material(code: str, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.code == code.upper()).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material
