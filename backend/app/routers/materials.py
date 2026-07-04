from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app import models, schemas

router = APIRouter(prefix="/materials", tags=["materials"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[schemas.MaterialOut])
def list_materials(include_inactive: bool = False, db: Session = Depends(get_db)):
    q = db.query(models.Material)
    if not include_inactive:
        q = q.filter(models.Material.is_active.is_(True))
    return q.order_by(models.Material.category, models.Material.name).all()


@router.post("/", response_model=schemas.MaterialOut)
def create_material(payload: schemas.MaterialCreate, db: Session = Depends(get_db)):
    if db.query(models.Material).filter(models.Material.name == payload.name).first():
        raise HTTPException(status_code=400, detail="A material with that name already exists")
    material = models.Material(**payload.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.patch("/{material_id}", response_model=schemas.MaterialOut)
def update_material(material_id: int, payload: schemas.MaterialUpdate, db: Session = Depends(get_db)):
    material = db.get(models.Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(material, field, value)
    db.commit()
    db.refresh(material)
    return material


@router.delete("/{material_id}")
def deactivate_material(material_id: int, db: Session = Depends(get_db)):
    """Soft delete - materials already used on past items must stay resolvable."""
    material = db.get(models.Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    material.is_active = False
    db.commit()
    return {"status": "deactivated"}
