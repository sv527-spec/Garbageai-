"""
Weight estimation service.

Default strategy: reference-object scaling from the 2D image (assumes a common reference — e.g. an
A4 sheet, a standard bottle cap, or the known dimensions of a smart-bin chute — is visible or the chute
opening is a known fixed size). This is a coarse estimate by design; an ESP32 load cell reading
(see `esp32_bridge.py`) always overrides it when available, per the spec.

TO IMPROVE: swap in a monocular depth estimation model (e.g. MiDaS) plus a material-density lookup table
to convert estimated volume -> weight, behind the same `estimate_weight_from_image()` signature.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

# Rough density table (g/cm^3) used to convert estimated volume to weight for the reference-scaling method.
_DENSITY_BY_CATEGORY = {
    "plastic": 0.95,
    "glass": 2.50,
    "steel": 7.85,
    "aluminium": 2.70,
    "iron": 7.87,
    "paper": 0.80,
    "cardboard": 0.35,
    "organic": 0.60,
    "textile": 0.30,
    "ewaste": 2.00,
}

# Assumed average item volume in cm^3 per category, derived from typical single-item waste
# (a bottle, a can, a sheet of paper, etc.) — used when no explicit scale reference is detected.
_ASSUMED_VOLUME_CM3 = {
    "plastic": 500,
    "glass": 300,
    "steel": 200,
    "aluminium": 250,
    "iron": 200,
    "paper": 400,
    "cardboard": 1500,
    "organic": 600,
    "textile": 800,
    "ewaste": 300,
}


@dataclass
class WeightEstimate:
    weight_kg: float
    confidence: float
    source: str  # "vision" | "load_cell" | "manual"


def estimate_weight_from_image(image_bytes: bytes, category: str) -> WeightEstimate:
    """Coarse single-item weight estimate from image + material category.

    This deliberately does not attempt precise volumetric reconstruction (that needs depth data /
    multiple views); it gives a reasonable default so the pipeline is complete end to end, and is
    always superseded by a load-cell reading when one is present.
    """
    img = Image.open(__import__("io").BytesIO(image_bytes)).convert("L").resize((64, 64))
    arr = np.asarray(img) / 255.0
    # Use the fraction of frame occupied by non-background pixels as a very rough size proxy,
    # scaling the assumed volume up/down around its baseline.
    fill_ratio = float(np.mean(arr < 0.85))  # darker/occupied pixels vs bright background
    fill_ratio = min(max(fill_ratio, 0.05), 0.95)

    base_volume = _ASSUMED_VOLUME_CM3.get(category, 400)
    scaled_volume = base_volume * (0.5 + fill_ratio)  # 0.55x .. 1.45x baseline
    density = _DENSITY_BY_CATEGORY.get(category, 1.0)
    weight_g = scaled_volume * density
    weight_kg = round(weight_g / 1000, 4)

    return WeightEstimate(weight_kg=weight_kg, confidence=0.55, source="vision")


def weight_from_load_cell(grams: float) -> WeightEstimate:
    return WeightEstimate(weight_kg=round(grams / 1000, 4), confidence=0.97, source="load_cell")
