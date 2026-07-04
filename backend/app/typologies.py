"""
The five manufacturing-typology cost engines.

These are pure functions: numbers in, numbers out. No database access here
on purpose - resolving a material name to a rate (and deciding which unit
it's priced in) is the router's job, so this module stays trivial to test
and never silently guesses a price. Every function raises ValueError on
nonsensical input rather than producing a silently-wrong number.

Corrections made relative to the source document these were drafted from:
- The Horizontal Box edging formula referenced the wrong row's depth in the
  source document's compiled version (a copy-paste slip). Fixed here by
  construction - every value comes from this call's own inputs, so that
  class of bug can't happen.
- No margin or VAT is applied anywhere. These functions return cost only,
  per the agreed scope - quotation is a separate manual step outside the app.
- Every panel that contributes to board_area/linear_m is returned individually
  in "panels", not just summed, so the same calculation produces both the
  cost total and the raw material for a cutting list.
"""
from dataclasses import dataclass, field


@dataclass
class TypologyResult:
    panels: list[dict]
    labour_hours: float
    material_cost: float
    labour_cost: float
    total_cost: float
    board_area_m2: float | None = None
    linear_m: float | None = None
    consumables_cost: float = 0.0


def _panel(name: str, width_mm: float, length_mm: float, qty: int) -> dict:
    return {"name": name, "width_mm": width_mm, "length_mm": length_mm, "qty": qty}


def horizontal_box(
    length_mm: float, height_mm: float, depth_mm: float,
    separate_top: bool, drawers: int,
    board_rate_per_m2: float, edging_rate_per_m: float, drawer_hardware_cost_each: float,
    labour_rate: float, wastage: float = 1.10,
) -> TypologyResult:
    """Open-back/open-front carcass: counters, desks, benches, pedestals."""
    if length_mm <= 0 or height_mm <= 0 or depth_mm <= 0:
        raise ValueError("length, height, and depth must all be positive")
    if drawers < 0:
        raise ValueError("drawers cannot be negative")

    panels = [
        _panel("Side Panel", height_mm, depth_mm, 2),
        _panel("Front/Back Cladding Panel", length_mm, height_mm, 1),
    ]
    if not separate_top:
        panels.append(_panel("Top Panel", length_mm, depth_mm, 1))

    raw_area_m2 = sum((p["width_mm"] * p["length_mm"] / 1_000_000) * p["qty"] for p in panels)
    board_area_m2 = raw_area_m2 * wastage

    edging_m = ((length_mm * 2) + (height_mm * 4) + (depth_mm * 4)) / 1000
    labour_hours = 2 + (board_area_m2 * 0.5) + (drawers * 1.0)

    material_cost = (board_area_m2 * board_rate_per_m2) + (edging_m * edging_rate_per_m) + (drawers * drawer_hardware_cost_each)
    labour_cost = labour_hours * labour_rate

    return TypologyResult(
        panels=panels, board_area_m2=round(board_area_m2, 4), labour_hours=round(labour_hours, 2),
        material_cost=round(material_cost, 2), labour_cost=round(labour_cost, 2),
        total_cost=round(material_cost + labour_cost, 2),
    )


def vertical_box(
    width_mm: float, height_mm: float, depth_mm: float,
    shelves: int, doors: bool,
    board_rate_per_m2: float, edging_rate_per_m: float, hinge_hardware_cost: float,
    labour_rate: float, wastage: float = 1.10,
) -> TypologyResult:
    """Five-sided carcass with optional door: cabinets, towers, lockers, wardrobes."""
    if width_mm <= 0 or height_mm <= 0 or depth_mm <= 0:
        raise ValueError("width, height, and depth must all be positive")
    if shelves < 0:
        raise ValueError("shelves cannot be negative")

    panels = [
        _panel("Side Panel", height_mm, depth_mm, 2),
        _panel("Top Panel", width_mm, depth_mm, 1),
        _panel("Bottom Panel", width_mm, depth_mm, 1),
        _panel("Back Panel", width_mm, height_mm, 1),
    ]
    if shelves > 0:
        panels.append(_panel("Shelf", width_mm, depth_mm, shelves))
    if doors:
        panels.append(_panel("Door", width_mm, height_mm, 1))

    raw_area_m2 = sum((p["width_mm"] * p["length_mm"] / 1_000_000) * p["qty"] for p in panels)
    board_area_m2 = raw_area_m2 * wastage

    edging_m = (
        (height_mm * 4) + (width_mm * 4) + (depth_mm * 4)
        + (shelves * 2 * width_mm)
        + ((height_mm * 4 + width_mm * 4) if doors else 0)
    ) / 1000

    labour_hours = 3 + (board_area_m2 * 0.6) + (0.75 if doors else 0)

    material_cost = (board_area_m2 * board_rate_per_m2) + (edging_m * edging_rate_per_m) + (hinge_hardware_cost if doors else 0)
    labour_cost = labour_hours * labour_rate

    return TypologyResult(
        panels=panels, board_area_m2=round(board_area_m2, 4), labour_hours=round(labour_hours, 2),
        material_cost=round(material_cost, 2), labour_cost=round(labour_cost, 2),
        total_cost=round(material_cost + labour_cost, 2),
    )


def flat_framework(
    width_mm: float, height_mm: float, depth_mm: float,
    cross_rails: int, wheels: bool,
    profile_rate_per_m: float, finishing_rate_per_m: float,
    wheel_kit_cost: float, leveling_feet_cost: float,
    labour_rate: float, wastage: float = 1.10,
) -> TypologyResult:
    """Linear steel/timber skeleton, no sheet boxing: rails, trolleys, table frames."""
    if width_mm <= 0 or height_mm <= 0 or depth_mm <= 0:
        raise ValueError("width, height, and depth must all be positive")
    if cross_rails < 0:
        raise ValueError("cross_rails cannot be negative")

    linear_m = ((width_mm * 4) + (height_mm * 4) + (depth_mm * 4) + (cross_rails * width_mm)) / 1000 * wastage
    joints = 24 + (cross_rails * 2)
    labour_hours = 1.5 + (joints * 0.15) + (0.5 if wheels else 0)

    hardware_cost = wheel_kit_cost if wheels else leveling_feet_cost
    material_cost = (linear_m * profile_rate_per_m) + (linear_m * finishing_rate_per_m) + hardware_cost
    labour_cost = labour_hours * labour_rate

    # Framework members reported as linear runs, not W x L panels - qty tracks count of each run type.
    panels = [
        _panel("Width Rail", width_mm, None, 4),
        _panel("Height Post", height_mm, None, 4),
        _panel("Depth Rail", depth_mm, None, 4),
    ]
    if cross_rails > 0:
        panels.append(_panel("Cross Rail", width_mm, None, cross_rails))

    return TypologyResult(
        panels=panels, linear_m=round(linear_m, 3), labour_hours=round(labour_hours, 2),
        material_cost=round(material_cost, 2), labour_cost=round(labour_cost, 2),
        total_cost=round(material_cost + labour_cost, 2),
    )


def area_cladding(
    width_mm: float, height_mm: float,
    complexity_high: bool, perimeter_edging: bool,
    face_rate_per_m2: float, substructure_rate_per_m2: float, edge_trim_rate_per_m: float,
    labour_rate: float, wastage: float = 1.10,
) -> TypologyResult:
    """Flat 2D coverage over a substructure: slatwall, acoustic panels, suspended ceilings."""
    if width_mm <= 0 or height_mm <= 0:
        raise ValueError("width and height must both be positive")

    area_m2 = (width_mm * height_mm / 1_000_000) * wastage
    perimeter_m = ((width_mm * 2) + (height_mm * 2)) / 1000

    labour_hours = (1 + (area_m2 * 0.4)) * (1.35 if complexity_high else 1.0)
    if perimeter_edging:
        labour_hours += perimeter_m * 0.15

    material_cost = (area_m2 * face_rate_per_m2) + (area_m2 * substructure_rate_per_m2)
    if perimeter_edging:
        material_cost += perimeter_m * edge_trim_rate_per_m
    labour_cost = labour_hours * labour_rate

    panels = [_panel("Face Panel", width_mm, height_mm, 1)]

    return TypologyResult(
        panels=panels, board_area_m2=round(area_m2, 4), labour_hours=round(labour_hours, 2),
        material_cost=round(material_cost, 2), labour_cost=round(labour_cost, 2),
        total_cost=round(material_cost + labour_cost, 2),
    )


def framing_lines(
    opening_width_mm: float, opening_height_mm: float, mid_mullions: int,
    door_mechanism: str,  # "none" | "manual" | "automatic"
    frame_rate_per_m: float, glass_rate_per_m2: float,
    manual_door_kit_cost: float, automatic_door_kit_cost: float,
    labour_rate: float, wastage: float = 1.10,
) -> TypologyResult:
    """Heavy perimeter track holding glass/door infill: shopfronts, glass partitions."""
    if opening_width_mm <= 0 or opening_height_mm <= 0:
        raise ValueError("opening width and height must both be positive")
    if mid_mullions < 0:
        raise ValueError("mid_mullions cannot be negative")
    if door_mechanism not in ("none", "manual", "automatic"):
        raise ValueError('door_mechanism must be "none", "manual", or "automatic"')

    frame_run_m = (
        ((opening_width_mm * 2) + (opening_height_mm * 2)) + (mid_mullions * opening_height_mm)
    ) / 1000 * wastage
    glass_m2 = (opening_width_mm * opening_height_mm / 1_000_000) * wastage

    labour_hours = 4 + (frame_run_m * 0.4) + (glass_m2 * 0.5) + (0 if door_mechanism == "none" else 2.5)

    door_kit_cost = {"none": 0.0, "manual": manual_door_kit_cost, "automatic": automatic_door_kit_cost}[door_mechanism]
    material_cost = (frame_run_m * frame_rate_per_m) + (glass_m2 * glass_rate_per_m2) + door_kit_cost
    labour_cost = labour_hours * labour_rate

    panels = [
        _panel("Frame Perimeter Run", frame_run_m * 1000, None, 1),
        _panel("Glass Infill", opening_width_mm, opening_height_mm, 1),
    ]
    if mid_mullions > 0:
        panels.append(_panel("Mid-Mullion", opening_height_mm, None, mid_mullions))

    return TypologyResult(
        panels=panels, linear_m=round(frame_run_m, 3), labour_hours=round(labour_hours, 2),
        material_cost=round(material_cost, 2), labour_cost=round(labour_cost, 2),
        total_cost=round(material_cost + labour_cost, 2),
    )
