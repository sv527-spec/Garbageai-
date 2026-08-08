import io
from PIL import Image

from app.services.ai_classifier import classify


def _fake_image_bytes(color) -> bytes:
    img = Image.new("RGB", (128, 128), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_classify_returns_a_known_material_code():
    result = classify(_fake_image_bytes((200, 200, 200)))
    assert result.material_code in {
        "PET", "HDPE", "LDPE", "PP", "PS", "PC", "PVC", "ABS", "PLA",
        "GLASS", "STEEL", "ALUMINIUM", "IRON", "PAPER", "CARDBOARD", "ORGANIC", "TEXTILE", "EWASTE",
    }
    assert 0.0 <= result.confidence <= 1.0


def test_classify_rejects_invalid_bytes():
    import pytest
    with pytest.raises(ValueError):
        classify(b"not an image")
