from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.material import Material
from app.models.co2_factor import CO2Factor
from app.models.market_price import MarketPrice
from app.models.scan import Scan, WeightSource, ScanStatus
from app.models.esp32_device import ESP32Device
from app.schemas.scan import ScanCreateResponse, ScanOut
from app.services.ai_classifier import classify
from app.services.weight_estimator import estimate_weight_from_image, weight_from_load_cell
from app.services.co2_calculator import calculate_impact
from app.services.earnings_calculator import estimate_earnings
from app.services.esp32_bridge import push_command

router = APIRouter()

MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("", response_model=ScanCreateResponse, status_code=201)
async def create_scan(
    image: UploadFile = File(...),
    load_cell_grams: float | None = Form(default=None),
    device_uid: str | None = Form(default=None),
    disposal_mode: str = Form(default="recycle"),  # "recycle" | "reuse"
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported image type")

    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 8MB)")

    try:
        result = classify(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    material = db.query(Material).filter(Material.code == result.material_code).first()
    if not material:
        raise HTTPException(status_code=500, detail="Classifier returned an unseeded material code")

    # Weight: load cell (from an ESP32 bin) always wins over the vision estimate.
    if load_cell_grams is not None:
        weight = weight_from_load_cell(load_cell_grams)
    else:
        weight = estimate_weight_from_image(image_bytes, material.category.value)

    co2_factor = db.query(CO2Factor).filter(CO2Factor.material_id == material.id).first()
    impact = None
    if co2_factor:
        impact = calculate_impact(co2_factor, Decimal(str(weight.weight_kg)), mode=disposal_mode)

    price_row = (
        db.query(MarketPrice)
        .filter(MarketPrice.category == material.category.value)
        .order_by(MarketPrice.updated_at.desc())
        .first()
    )
    price_per_kg = price_row.price_per_kg if price_row else material.base_price_per_kg
    earnings = estimate_earnings(Decimal(str(weight.weight_kg)), price_per_kg)

    device = db.query(ESP32Device).filter(ESP32Device.device_uid == device_uid).first() if device_uid else None

    scan = Scan(
        user_id=user.id,
        material_id=material.id,
        confidence_score=Decimal(str(result.confidence)),
        estimated_weight_kg=Decimal(str(weight.weight_kg)),
        weight_source=WeightSource.LOAD_CELL if load_cell_grams is not None else WeightSource.VISION_ESTIMATE,
        weight_confidence=Decimal(str(weight.confidence)),
        co2_saved_kg=impact.co2_saved_kg if impact else None,
        earnings_estimate=earnings,
        device_id=device.id if device else None,
        status=ScanStatus.CLASSIFIED,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Tell the bin which compartment to open. Try a direct push (works on a shared local network);
    # otherwise queue it for the bin's next poll, which is the path that works when this backend is
    # hosted in the cloud and the bin sits behind NAT. Either way a bin problem never fails the scan —
    # the user still gets their classification result and can dispose manually.
    if device:
        command = {"material_category": material.category.value, "scan_id": str(scan.id)}
        pushed = await push_command(device.ip_address, command) if device.ip_address else False
        if not pushed:
            device.pending_category = material.category.value
            device.pending_scan_id = str(scan.id)
            device.pending_created_at = datetime.now(timezone.utc)
            db.commit()

    return ScanCreateResponse(
        id=scan.id,
        material=material,
        confidence_score=scan.confidence_score,
        estimated_weight_kg=scan.estimated_weight_kg,
        weight_source=scan.weight_source,
        weight_confidence=scan.weight_confidence,
        co2_saved_kg=impact.co2_saved_kg if impact else None,
        tree_equivalent=impact.tree_equivalent if impact else None,
        energy_saved_kwh=impact.energy_saved_kwh if impact else None,
        landfill_volume_reduced_l=impact.landfill_volume_reduced_l if impact else None,
        earnings_estimate=scan.earnings_estimate,
        status=scan.status,
        created_at=scan.created_at,
        calculation_notes={
            "classifier_features": result.features,
            "impact": impact.notes if impact else None,
            "price_per_kg_used": str(price_per_kg),
            "price_source": price_row.source if price_row else "material_default",
        },
    )


@router.get("", response_model=list[ScanOut])
def list_my_scans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Scan).filter(Scan.user_id == user.id).order_by(Scan.created_at.desc()).all()


@router.get("/{scan_id}", response_model=ScanOut)
def get_scan(scan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
