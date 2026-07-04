from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app import models, schemas, component_service
from app.cutting import build_cutting_list

router = APIRouter(tags=["items"], dependencies=[Depends(get_current_user)])


def _compute_and_build(db: Session, project_id: int, payload: schemas.ItemCreate) -> models.Item:
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    item = models.Item(project_id=project_id, name=payload.name, quantity=payload.quantity)
    db.add(item)
    db.flush()  # get item.id without committing yet

    for comp_payload in payload.components:
        try:
            result = component_service.compute_component(db, comp_payload.typology, comp_payload.inputs)
        except (KeyError, ValueError) as exc:
            db.rollback()
            missing = f"Missing input: {exc}" if isinstance(exc, KeyError) else str(exc)
            raise HTTPException(status_code=400, detail=missing)

        db.add(models.Component(
            item_id=item.id, typology=comp_payload.typology, name=comp_payload.name,
            inputs=comp_payload.inputs, derived_panels=result.panels,
            board_area_m2=result.board_area_m2, linear_m=result.linear_m,
            labour_hours=result.labour_hours, material_cost=result.material_cost,
            labour_cost=result.labour_cost, total_cost=result.total_cost,
        ))

    db.commit()
    db.refresh(item)
    return item


@router.post("/projects/{project_id}/items", response_model=schemas.ItemOut)
def create_item(project_id: int, payload: schemas.ItemCreate, db: Session = Depends(get_db)):
    return _compute_and_build(db, project_id, payload)


@router.get("/projects/{project_id}/items", response_model=list[schemas.ItemOut])
def list_items(project_id: int, db: Session = Depends(get_db)):
    return db.query(models.Item).filter(models.Item.project_id == project_id).all()


@router.get("/projects/{project_id}/cost-analysis")
def cost_analysis(project_id: int, db: Session = Depends(get_db)):
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    items_out = []
    project_total = 0.0
    for item in project.items:
        unit_cost = sum(c.total_cost for c in item.components)
        line_total = unit_cost * item.quantity
        project_total += line_total
        items_out.append({
            "item_id": item.id, "name": item.name, "quantity": item.quantity,
            "unit_cost": round(unit_cost, 2), "line_total": round(line_total, 2),
            "components": [
                {"typology": c.typology, "name": c.name, "material_cost": c.material_cost,
                 "labour_cost": c.labour_cost, "total_cost": c.total_cost}
                for c in item.components
            ],
        })
    return {"project_id": project_id, "project_name": project.name, "items": items_out, "project_total": round(project_total, 2)}


@router.get("/items/{item_id}/cutting-list")
def cutting_list(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    kerf_mm = db.get(models.Setting, "kerf_mm")
    kerf_mm = kerf_mm.value if kerf_mm else 3.5

    components_out = []
    for c in item.components:
        row = {"component": c.name or c.typology.value, "typology": c.typology, "rows": []}
        # Sheet-based typologies carry their board material name under "board_material"
        # (or "face_material" for Area Cladding); linear typologies have no cutting-list
        # orientation step, so we surface their panel list as-is (no sheet to nest against).
        material_key = c.inputs.get("board_material") or c.inputs.get("face_material")
        if material_key:
            material = db.query(models.Material).filter(models.Material.name == material_key).first()
            if material and material.length_mm and material.width_mm:
                try:
                    row["rows"] = build_cutting_list(c.derived_panels, material.width_mm, material.length_mm, kerf_mm)
                except ValueError as exc:
                    row["error"] = str(exc)
            else:
                row["error"] = f'Material "{material_key}" is missing sheet dimensions.'
        else:
            row["rows"] = [p for p in c.derived_panels]  # linear members - cut to length, no nesting
        components_out.append(row)

    return {"item_id": item_id, "item_name": item.name, "quantity": item.quantity, "components": components_out}
