"""
Cutting-list yield and orientation logic.

This is the piece that replaces the manual "which way do I cut this" button
from the original spreadsheet. Given one panel's size and the sheet size of
its assigned material, compute how many panels fit per sheet in both
orientations (accounting for saw kerf) and pick whichever orientation wins.
Pure math - no drawing-reading, no AI judgement.

This only applies to sheet-based panels (Horizontal Box, Vertical Box, Area
Cladding, and the glass infill of Framing Lines). Flat Framework's linear
stock members don't have an orientation choice - they're just cut to length.
"""
from dataclasses import dataclass
import math


@dataclass
class OrientationResult:
    orientation: str  # "as_drawn" or "rotated"
    fit_per_sheet: int
    sheets_needed: int


def best_orientation_yield(
    panel_width_mm: float, panel_length_mm: float,
    sheet_width_mm: float, sheet_length_mm: float,
    qty_needed: int, kerf_mm: float = 3.5,
) -> OrientationResult:
    if panel_width_mm <= 0 or panel_length_mm <= 0:
        raise ValueError("panel dimensions must be positive")
    if sheet_width_mm <= 0 or sheet_length_mm <= 0:
        raise ValueError("sheet dimensions must be positive")
    if qty_needed < 0:
        raise ValueError("qty_needed cannot be negative")

    def fit_count(pw: float, pl: float) -> int:
        across = math.floor((sheet_width_mm + kerf_mm) / (pw + kerf_mm))
        down = math.floor((sheet_length_mm + kerf_mm) / (pl + kerf_mm))
        return max(across, 0) * max(down, 0)

    as_drawn = fit_count(panel_width_mm, panel_length_mm)
    rotated = fit_count(panel_length_mm, panel_width_mm)

    if rotated > as_drawn:
        fit_per_sheet, orientation = rotated, "rotated"
    else:
        fit_per_sheet, orientation = as_drawn, "as_drawn"

    if fit_per_sheet == 0:
        raise ValueError(
            f"panel {panel_width_mm}x{panel_length_mm}mm does not fit on a "
            f"{sheet_width_mm}x{sheet_length_mm}mm sheet in either orientation"
        )

    sheets_needed = math.ceil(qty_needed / fit_per_sheet) if qty_needed > 0 else 0
    return OrientationResult(orientation=orientation, fit_per_sheet=fit_per_sheet, sheets_needed=sheets_needed)


def build_cutting_list(panels: list[dict], sheet_width_mm: float, sheet_length_mm: float, kerf_mm: float = 3.5) -> list[dict]:
    """
    panels: list of {name, width_mm, length_mm, qty} for ONE material (sheet-based
    panels only - skip any panel with length_mm is None, which signals a linear
    member from Flat Framework/Framing Lines rather than a sheet panel).
    Returns one cutting-list row per panel with its orientation and sheet count.
    """
    rows = []
    for p in panels:
        if p.get("length_mm") is None:
            continue  # linear stock member, not a sheet panel
        result = best_orientation_yield(
            p["width_mm"], p["length_mm"], sheet_width_mm, sheet_length_mm, p["qty"], kerf_mm
        )
        rows.append({
            "panel": p["name"],
            "width_mm": p["width_mm"],
            "length_mm": p["length_mm"],
            "qty": p["qty"],
            "orientation": result.orientation,
            "fit_per_sheet": result.fit_per_sheet,
            "sheets_needed": result.sheets_needed,
        })
    return rows
