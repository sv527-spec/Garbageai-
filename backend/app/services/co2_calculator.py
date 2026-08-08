"""
CO2 / energy / landfill impact calculator.

Reads factors from the `co2_factors` table (admin-editable, source-cited) rather than hardcoding them,
per the spec's transparency requirement. `seed_data.py` populates initial values sourced from published
EPA WARM model and CPCB (Central Pollution Control Board, India) recycling factor tables — see the
`source_note` column on each row for the citation.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.models.co2_factor import CO2Factor

# 1 tree absorbs roughly 21 kg CO2/year (commonly cited EPA reforestation figure) — used only for the
# user-facing "trees equivalent" framing, not for the underlying CO2 math.
_KG_CO2_PER_TREE_YEAR = Decimal("21.0")


@dataclass
class ImpactEstimate:
    co2_saved_kg: Decimal
    tree_equivalent: Decimal
    energy_saved_kwh: Decimal
    landfill_volume_reduced_l: Decimal
    notes: dict


def calculate_impact(factor: CO2Factor, weight_kg: Decimal, mode: str = "recycle") -> ImpactEstimate:
    """mode: 'recycle' or 'reuse' — reuse typically prevents more emissions than recycling."""
    per_kg = factor.co2_saved_reuse_per_kg if mode == "reuse" else factor.co2_saved_recycle_per_kg
    co2_saved = (per_kg * weight_kg).quantize(Decimal("0.0001"))
    trees = (co2_saved / _KG_CO2_PER_TREE_YEAR).quantize(Decimal("0.000001"))
    energy = (factor.energy_saved_per_kg_kwh * weight_kg).quantize(Decimal("0.0001"))
    landfill = (factor.landfill_volume_reduced_per_kg_l * weight_kg).quantize(Decimal("0.0001"))

    return ImpactEstimate(
        co2_saved_kg=co2_saved,
        tree_equivalent=trees,
        energy_saved_kwh=energy,
        landfill_volume_reduced_l=landfill,
        notes={
            "mode": mode,
            "co2_factor_per_kg": str(per_kg),
            "source": factor.source_note,
            "tree_equivalence_basis": "1 tree absorbs ~21 kg CO2/year (EPA)",
        },
    )
