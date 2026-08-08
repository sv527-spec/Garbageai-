"""
Seeds materials, CO2/impact factors, and starting market prices.

Run with: `python -m app.seed_data` (inside the backend venv/container, after migrations).

CO2/energy/landfill factors are approximate figures compiled from the US EPA WARM (Waste Reduction
Model) v15 emission factor tables and CPCB (India) recycling guidance documents — cite/replace with
your own verified figures before relying on this for compliance reporting; the `source_note` field
exists specifically so these numbers stay auditable and admin-editable rather than buried in code.
"""
from decimal import Decimal

from app.core.database import SessionLocal, engine, Base
from app.models.material import Material, MaterialCategory, PolymerType
from app.models.co2_factor import CO2Factor
from app.models.market_price import MarketPrice

# (code, name, category, polymer_type, biodegradable, recyclable, reusable, description,
#  disposal, recycling_instr, base_price_per_kg,
#  co2_recycle, co2_reuse, energy_kwh, landfill_l, tree_eq_source)
SEED = [
    ("PET", "PET Plastic (Polyethylene Terephthalate)", MaterialCategory.PLASTIC, PolymerType.PET,
     False, True, True, "Clear plastic used in bottles and containers.",
     "Rinse and flatten before disposal.", "Accepted by most municipal recycling programs.",
     15.00, 1.5, 2.0, 3.8, 2.5, "EPA WARM v15 (PET)"),
    ("HDPE", "HDPE Plastic (High-Density Polyethylene)", MaterialCategory.PLASTIC, PolymerType.HDPE,
     False, True, True, "Opaque plastic used in milk jugs, detergent bottles.",
     "Rinse before disposal.", "Widely recyclable; check local facility acceptance.",
     18.00, 1.4, 1.9, 3.5, 2.3, "EPA WARM v15 (HDPE)"),
    ("LDPE", "LDPE Plastic (Low-Density Polyethylene)", MaterialCategory.PLASTIC, PolymerType.LDPE,
     False, True, False, "Flexible plastic used in bags and film.",
     "Keep dry and clean.", "Accepted at select drop-off points only.",
     8.00, 1.2, 1.6, 3.0, 2.0, "EPA WARM v15 (LDPE)"),
    ("PP", "PP Plastic (Polypropylene)", MaterialCategory.PLASTIC, PolymerType.PP,
     False, True, True, "Rigid plastic used in food containers, bottle caps.",
     "Rinse before disposal.", "Recyclable at facilities accepting PP (code 5).",
     12.00, 1.3, 1.7, 3.2, 2.1, "EPA WARM v15 (PP)"),
    ("PS", "PS Plastic (Polystyrene)", MaterialCategory.PLASTIC, PolymerType.PS,
     False, False, False, "Rigid or foam plastic used in packaging, cups.",
     "Dispose as general waste; rarely recycled.", "Not accepted by most municipal programs.",
     3.00, 0.6, 0.8, 1.5, 1.0, "EPA WARM v15 (PS)"),
    ("PC", "PC Plastic (Polycarbonate)", MaterialCategory.PLASTIC, PolymerType.PC,
     False, False, True, "Durable plastic used in eyewear, electronics housings.",
     "Dispose as e-waste-adjacent if from electronics.", "Limited specialty recycling only.",
     5.00, 0.7, 1.0, 1.8, 1.1, "Estimated from generic plastics WARM factor"),
    ("PVC", "PVC Plastic (Polyvinyl Chloride)", MaterialCategory.PLASTIC, PolymerType.PVC,
     False, False, False, "Plastic used in pipes, cables.",
     "Do not burn; dispose via hazardous/special waste stream.", "Not municipally recyclable.",
     4.00, 0.5, 0.7, 1.4, 0.9, "Estimated from generic plastics WARM factor"),
    ("ABS", "ABS Plastic", MaterialCategory.PLASTIC, PolymerType.ABS,
     False, False, True, "Engineering plastic used in toys, electronics casings.",
     "Dispose as e-waste-adjacent if from electronics.", "Limited specialty recycling only.",
     6.00, 0.7, 1.0, 1.8, 1.1, "Estimated from generic plastics WARM factor"),
    ("PLA", "PLA Plastic (Polylactic Acid)", MaterialCategory.PLASTIC, PolymerType.PLA,
     True, True, False, "Biodegradable bioplastic used in 3D printing, compostable packaging.",
     "Industrial composting preferred over landfill.", "Compost at facilities accepting bioplastics.",
     10.00, 0.9, 1.1, 2.0, 3.0, "Estimated compostable-plastics factor"),
    ("GLASS", "Glass", MaterialCategory.GLASS, None,
     False, True, True, "Glass bottles, jars, containers.",
     "Rinse; separate by color if required locally.", "Infinitely recyclable without quality loss.",
     2.00, 0.3, 0.6, 2.7, 1.8, "EPA WARM v15 (Glass)"),
    ("STEEL", "Steel", MaterialCategory.STEEL, None,
     False, True, True, "Steel cans, scrap, fittings.",
     "Remove labels/contents before disposal.", "High-value scrap metal recycling.",
     25.00, 1.8, 2.4, 5.0, 3.0, "EPA WARM v15 (Steel)"),
    ("ALUMINIUM", "Aluminium", MaterialCategory.ALUMINIUM, None,
     False, True, True, "Aluminium cans, foil, scrap.",
     "Rinse cans; keep foil clean.", "Among the most valuable/efficient recyclables.",
     110.00, 8.1, 9.5, 14.0, 3.5, "EPA WARM v15 (Aluminium)"),
    ("IRON", "Iron", MaterialCategory.IRON, None,
     False, True, True, "Iron scrap and fittings.",
     "Sell to scrap metal dealers/collection drives.", "Standard scrap metal recycling.",
     22.00, 1.7, 2.2, 4.8, 2.9, "EPA WARM v15 (Ferrous metals)"),
    ("PAPER", "Paper", MaterialCategory.PAPER, None,
     True, True, True, "Newspaper, office paper, printed material.",
     "Keep dry; separate from cardboard if required locally.", "Standard curbside/drop-off recycling.",
     8.00, 0.9, 1.2, 2.5, 3.3, "EPA WARM v15 (Mixed paper)"),
    ("CARDBOARD", "Cardboard", MaterialCategory.CARDBOARD, None,
     True, True, True, "Corrugated boxes and packaging.",
     "Flatten before disposal.", "Standard curbside/drop-off recycling.",
     9.00, 1.1, 1.4, 2.8, 3.6, "EPA WARM v15 (Corrugated cardboard)"),
    ("ORGANIC", "Organic Waste", MaterialCategory.ORGANIC, None,
     True, False, False, "Food scraps, garden waste.",
     "Compost where possible.", "Not recyclable in the material sense; divert to composting.",
     0.00, 0.4, 0.0, 0.5, 1.2, "EPA WARM v15 (Food waste, composting pathway)"),
    ("TEXTILE", "Textile", MaterialCategory.TEXTILE, None,
     False, False, True, "Clothing, fabric scraps.",
     "Donate if wearable; otherwise dispose as general waste.", "Limited textile-recycling drop-offs only.",
     6.00, 0.5, 1.3, 3.0, 2.0, "Estimated from EPA WARM textiles category"),
    ("EWASTE", "Electronic Waste", MaterialCategory.EWASTE, None,
     False, True, True, "Old phones, cables, small electronics.",
     "Do NOT dispose in general waste; use certified e-waste collection only.",
     "Certified e-waste recyclers recover metals and prevent toxic leaching.",
     40.00, 3.0, 4.0, 20.0, 4.0, "Estimated from EPA WARM electronics category"),
]

MARKET_PRICE_CATEGORIES = ["plastic", "glass", "paper", "metal", "cardboard"]
CATEGORY_STARTING_PRICE = {"plastic": 12.0, "glass": 2.0, "paper": 8.0, "metal": 40.0, "cardboard": 9.0}


def seed():
    Base.metadata.create_all(bind=engine)  # convenience for first-run without Alembic; migrations still recommended
    db = SessionLocal()
    try:
        for (code, name, category, polymer, biodeg, recyc, reuse, desc, disposal, recyc_instr,
             price, co2_recycle, co2_reuse, energy, landfill, source) in SEED:
            if db.query(Material).filter(Material.code == code).first():
                continue
            material = Material(
                code=code, name=name, category=category, polymer_type=polymer,
                biodegradable=biodeg, recyclable=recyc, reusable=reuse,
                description=desc, disposal_instructions=disposal, recycling_instructions=recyc_instr,
                base_price_per_kg=Decimal(str(price)),
            )
            db.add(material)
            db.flush()  # get material.id
            db.add(CO2Factor(
                material_id=material.id,
                co2_saved_recycle_per_kg=Decimal(str(co2_recycle)),
                co2_saved_reuse_per_kg=Decimal(str(co2_reuse)),
                energy_saved_per_kg_kwh=Decimal(str(energy)),
                landfill_volume_reduced_per_kg_l=Decimal(str(landfill)),
                tree_equivalent_per_kg=Decimal(str(co2_recycle)) / Decimal("21.0"),
                source_note=source,
            ))

        for category in MARKET_PRICE_CATEGORIES:
            if db.query(MarketPrice).filter(MarketPrice.category == category).first():
                continue
            db.add(MarketPrice(
                category=category,
                price_per_kg=Decimal(str(CATEGORY_STARTING_PRICE[category])),
                currency="INR",
                source="admin",
            ))

        db.commit()
        print(f"Seeded {len(SEED)} materials and {len(MARKET_PRICE_CATEGORIES)} market prices.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
