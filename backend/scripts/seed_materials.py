"""
One-off script: loads Shopfitting_Master_Price_List_Merged.xlsx into the
sfc_materials table. Run once against a fresh database (after `alembic
upgrade head`), or again later if you want to bulk-reset from the sheet -
existing rows with matching names are updated in place, not duplicated.

Usage:
    cd backend
    python scripts/seed_materials.py "../Shopfitting_Master_Price_List_Merged.xlsx"
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import openpyxl
from app.database import SessionLocal
from app import models


def main(xlsx_path: str):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Materials"]
    db = SessionLocal()
    created, updated = 0, 0
    try:
        for row in ws.iter_rows(min_row=2, values_only=True):
            category, description, supplied_as, length, width, thickness, cost, source = row
            if not description:
                continue
            existing = db.query(models.Material).filter(models.Material.name == description).first()
            if existing:
                existing.category, existing.supplied_as = category, supplied_as
                existing.length_mm, existing.width_mm, existing.thickness_mm = length, width, thickness
                existing.cost = cost
                updated += 1
            else:
                db.add(models.Material(
                    category=category, name=description, supplied_as=supplied_as,
                    length_mm=length, width_mm=width, thickness_mm=thickness,
                    cost=cost, unit="per_m2" if supplied_as == "Sheet" else "each",
                ))
                created += 1
        db.commit()

        labour_ws = wb["Labour"]
        labour_rate = labour_ws["B2"].value
        if labour_rate:
            setting = db.get(models.Setting, "labour_rate")
            if setting:
                setting.value = labour_rate
            else:
                db.add(models.Setting(key="labour_rate", value=labour_rate, description="Standard burdened labour rate per hour (ZAR)"))
            db.commit()

        print(f"Materials: {created} created, {updated} updated. Labour rate set to {labour_rate}.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/seed_materials.py <path-to-merged-xlsx>")
        sys.exit(1)
    main(sys.argv[1])
