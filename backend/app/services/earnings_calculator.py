"""Converts weight + market price into an earnings estimate. Prices are admin/API-editable, never hardcoded."""
from __future__ import annotations

from decimal import Decimal


def estimate_earnings(weight_kg: Decimal, price_per_kg: Decimal) -> Decimal:
    return (weight_kg * price_per_kg).quantize(Decimal("0.01"))
