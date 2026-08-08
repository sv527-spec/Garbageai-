"""
Waste image classification service.

This module defines the stable interface (`classify`) that the rest of the app depends on.
The shipped implementation is a deterministic, explainable HEURISTIC baseline — color histogram +
texture features mapped to material classes — chosen so the whole platform runs end-to-end without a
GPU, a trained checkpoint, or a labeled dataset.

TO GO TO PRODUCTION ACCURACY:
  1. Train a YOLOv8/v11 classification or detection model on a labeled dataset (TrashNet, TACO, or your
     own captured North-East-India waste photos).
  2. Export to ONNX.
  3. Replace the body of `classify()` with an ONNX Runtime session call, keeping the same return type
     (ClassificationResult). Nothing else in the codebase needs to change.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np
from PIL import Image
from skimage import color as skcolor

# Material codes must match app.models.material.Material.code seed values.
_MATERIAL_PROFILES = {
    # code: (mean_hue_deg, mean_saturation, mean_value, texture_std_threshold)
    "PET": (200, 0.15, 0.85, 0.10),        # clear/blue-ish, glossy, low texture variance
    "HDPE": (0, 0.05, 0.90, 0.08),         # white/opaque, low saturation
    "GLASS": (140, 0.10, 0.70, 0.05),      # green/clear, very low texture variance (smooth)
    "ALUMINIUM": (0, 0.02, 0.80, 0.12),    # metallic gray, low saturation, mid texture (reflections)
    "STEEL": (210, 0.05, 0.55, 0.15),
    "PAPER": (40, 0.10, 0.85, 0.20),       # beige/white, higher texture (fibrous)
    "CARDBOARD": (30, 0.25, 0.55, 0.25),   # brown, high texture
    "ORGANIC": (90, 0.35, 0.45, 0.30),     # green/brown, highest texture variance
    "TEXTILE": (250, 0.30, 0.50, 0.28),
    "EWASTE": (220, 0.10, 0.30, 0.22),     # dark, low value
}


@dataclass
class ClassificationResult:
    material_code: str
    confidence: float
    features: dict  # raw features used, for the "how we got this" transparency panel


def _extract_features(image: Image.Image) -> dict:
    img = image.convert("RGB").resize((128, 128))
    arr = np.asarray(img) / 255.0
    hsv = skcolor.rgb2hsv(arr)
    mean_hue = float(np.mean(hsv[:, :, 0]) * 360)
    mean_sat = float(np.mean(hsv[:, :, 1]))
    mean_val = float(np.mean(hsv[:, :, 2]))
    gray = skcolor.rgb2gray(arr)
    texture_std = float(np.std(gray))
    return {
        "mean_hue_deg": round(mean_hue, 2),
        "mean_saturation": round(mean_sat, 4),
        "mean_value": round(mean_val, 4),
        "texture_std": round(texture_std, 4),
    }


def _score(features: dict, profile: tuple) -> float:
    hue, sat, val, tex = profile
    hue_diff = min(abs(features["mean_hue_deg"] - hue), 360 - abs(features["mean_hue_deg"] - hue)) / 180
    sat_diff = abs(features["mean_saturation"] - sat)
    val_diff = abs(features["mean_value"] - val)
    tex_diff = abs(features["texture_std"] - tex)
    distance = 0.4 * hue_diff + 0.25 * sat_diff + 0.15 * val_diff + 0.2 * tex_diff
    return max(0.0, 1.0 - distance)


def classify(image_bytes: bytes) -> ClassificationResult:
    """Classify a waste image into one of the seeded material codes.

    Raises ValueError if the bytes are not a decodable image.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not decode image: {exc}") from exc

    features = _extract_features(image)
    scores = {code: _score(features, profile) for code, profile in _MATERIAL_PROFILES.items()}
    best_code = max(scores, key=scores.get)
    best_score = scores[best_code]

    # Normalize confidence into a believable band; heuristic models should not claim high certainty.
    confidence = round(min(0.95, max(0.35, best_score)), 4)

    return ClassificationResult(material_code=best_code, confidence=confidence, features=features)
