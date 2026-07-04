"""
Bridges a Component's raw typology inputs (dimensions + material names as
strings) to the pure-math typology engine: looks up each named material,
converts its supplied cost to the rate the engine needs, pulls the labour
rate from Settings, and returns a TypologyResult ready to persist.
"""
from sqlalchemy.orm import Session

from app import models, typologies, pricing


def _get_material(db: Session, name: str) -> models.Material:
    material = db.query(models.Material).filter(models.Material.name == name, models.Material.is_active.is_(True)).first()
    if not material:
        raise ValueError(f'Material "{name}" was not found (or is inactive). Check the Materials screen.')
    return material


def _get_setting(db: Session, key: str, default: float) -> float:
    setting = db.get(models.Setting, key)
    return setting.value if setting else default


def _apply_consumables(db: Session, result: typologies.TypologyResult) -> typologies.TypologyResult:
    """Adds a flat consumables markup (screws, glue, sealant, tape, sandpaper,
    etc.) as a percentage of material cost. These items aren't individually
    priced anywhere in the typology engines, so this is a blanket allowance
    rather than a measured quantity - editable via Settings, same as
    labour_rate/wastage_factor, and intended to be recalibrated against real
    jobs rather than trusted as-is."""
    consumables_pct = _get_setting(db, "consumables_pct", 5.0)
    result.consumables_cost = round(result.material_cost * consumables_pct / 100, 2)
    result.total_cost = round(result.total_cost + result.consumables_cost, 2)
    return result


def compute_component(db: Session, typology: models.Typology, inputs: dict) -> typologies.TypologyResult:
    labour_rate = _get_setting(db, "labour_rate", 350.0)
    wastage = _get_setting(db, "wastage_factor", 1.10)

    if typology == models.Typology.horizontal_box:
        board = _get_material(db, inputs["board_material"])
        edging = _get_material(db, inputs["edging_material"])
        drawers = int(inputs.get("drawers", 0))
        drawer_cost = 0.0
        if drawers > 0:
            drawer_cost = pricing.rate_each(_get_material(db, inputs["drawer_hardware_material"]))
        result = typologies.horizontal_box(
            length_mm=inputs["length_mm"], height_mm=inputs["height_mm"], depth_mm=inputs["depth_mm"],
            separate_top=bool(inputs.get("separate_top", False)), drawers=drawers,
            board_rate_per_m2=pricing.rate_per_m2(board), edging_rate_per_m=pricing.rate_per_lm(edging),
            drawer_hardware_cost_each=drawer_cost, labour_rate=labour_rate, wastage=wastage,
        )
        return _apply_consumables(db, result)

    if typology == models.Typology.vertical_box:
        board = _get_material(db, inputs["board_material"])
        edging = _get_material(db, inputs["edging_material"])
        doors = bool(inputs.get("doors", False))
        hinge_cost = 0.0
        if doors:
            hinge_cost = pricing.rate_each(_get_material(db, inputs["hinge_hardware_material"]))
        result = typologies.vertical_box(
            width_mm=inputs["width_mm"], height_mm=inputs["height_mm"], depth_mm=inputs["depth_mm"],
            shelves=int(inputs.get("shelves", 0)), doors=doors,
            board_rate_per_m2=pricing.rate_per_m2(board), edging_rate_per_m=pricing.rate_per_lm(edging),
            hinge_hardware_cost=hinge_cost, labour_rate=labour_rate, wastage=wastage,
        )
        return _apply_consumables(db, result)

    if typology == models.Typology.flat_framework:
        profile = _get_material(db, inputs["profile_material"])
        finishing = _get_material(db, inputs["finishing_material"])
        wheels = bool(inputs.get("wheels", False))
        wheel_kit_cost = pricing.rate_each(_get_material(db, inputs["wheel_kit_material"])) if wheels else 0.0
        leveling_cost = pricing.rate_each(_get_material(db, inputs["leveling_feet_material"])) if not wheels else 0.0
        result = typologies.flat_framework(
            width_mm=inputs["width_mm"], height_mm=inputs["height_mm"], depth_mm=inputs["depth_mm"],
            cross_rails=int(inputs.get("cross_rails", 0)), wheels=wheels,
            profile_rate_per_m=pricing.rate_per_lm(profile), finishing_rate_per_m=pricing.rate_per_lm(finishing),
            wheel_kit_cost=wheel_kit_cost, leveling_feet_cost=leveling_cost, labour_rate=labour_rate, wastage=wastage,
        )
        return _apply_consumables(db, result)

    if typology == models.Typology.area_cladding:
        face = _get_material(db, inputs["face_material"])
        substructure = _get_material(db, inputs["substructure_material"])
        perimeter_edging = bool(inputs.get("perimeter_edging", False))
        edge_trim_rate = 0.0
        if perimeter_edging:
            edge_trim_rate = pricing.rate_per_lm(_get_material(db, inputs["edge_trim_material"]))
        result = typologies.area_cladding(
            width_mm=inputs["width_mm"], height_mm=inputs["height_mm"],
            complexity_high=bool(inputs.get("complexity_high", False)), perimeter_edging=perimeter_edging,
            face_rate_per_m2=pricing.rate_per_m2(face), substructure_rate_per_m2=pricing.rate_per_m2(substructure),
            edge_trim_rate_per_m=edge_trim_rate, labour_rate=labour_rate, wastage=wastage,
        )
        return _apply_consumables(db, result)

    if typology == models.Typology.framing_lines:
        frame = _get_material(db, inputs["frame_material"])
        glass = _get_material(db, inputs["glass_material"])
        door_mechanism = inputs.get("door_mechanism", "none")
        manual_cost = pricing.rate_each(_get_material(db, inputs["manual_door_kit_material"])) if door_mechanism == "manual" else 0.0
        auto_cost = pricing.rate_each(_get_material(db, inputs["automatic_door_kit_material"])) if door_mechanism == "automatic" else 0.0
        result = typologies.framing_lines(
            opening_width_mm=inputs["opening_width_mm"], opening_height_mm=inputs["opening_height_mm"],
            mid_mullions=int(inputs.get("mid_mullions", 0)), door_mechanism=door_mechanism,
            frame_rate_per_m=pricing.rate_per_lm(frame), glass_rate_per_m2=pricing.rate_per_m2(glass),
            manual_door_kit_cost=manual_cost, automatic_door_kit_cost=auto_cost, labour_rate=labour_rate, wastage=wastage,
        )
        return _apply_consumables(db, result)

    raise ValueError(f"Unknown typology: {typology}")
