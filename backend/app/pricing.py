"""
Converts a Material row's "cost as supplied" (e.g. R850 for a whole 2440x1220
sheet, R280 for a 50m roll) into the per-m2 / per-linear-metre rate the
typology engine needs. Raises a clear error rather than guessing when a
material is missing the dimension data required for the conversion - the
same "no silent guessing with real money" rule used throughout this app.
"""
from app.models import Material


def rate_per_m2(material: Material) -> float:
    if material.length_mm and material.width_mm:
        area_m2 = (material.length_mm * material.width_mm) / 1_000_000
        if area_m2 > 0:
            return material.cost / area_m2
    raise ValueError(
        f'Material "{material.name}" is missing Length/Width, so a per-m2 rate '
        f"can't be computed. Add its sheet dimensions in the Materials screen."
    )


def rate_per_lm(material: Material) -> float:
    if material.length_mm:
        length_m = material.length_mm / 1000
        if length_m > 0:
            return material.cost / length_m
    raise ValueError(
        f'Material "{material.name}" is missing Length, so a per-linear-metre rate '
        f"can't be computed. Add its supplied length in the Materials screen."
    )


def rate_each(material: Material) -> float:
    return material.cost
