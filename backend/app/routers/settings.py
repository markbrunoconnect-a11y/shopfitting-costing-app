from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app import models, schemas

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[schemas.SettingOut])
def list_settings(db: Session = Depends(get_db)):
    """
    Business-wide calibration numbers (wastage factor, kerf, consumables
    markup, base labour rate) that feed every cost calculation. Previously
    only editable via direct database access - this is the "update without
    touching the app" screen promised for Materials, now extended to these.
    """
    return db.query(models.Setting).order_by(models.Setting.key).all()


@router.patch("/{key}", response_model=schemas.SettingOut)
def update_setting(key: str, payload: schemas.SettingUpdate, db: Session = Depends(get_db)):
    setting = db.get(models.Setting, key)
    if not setting:
        raise HTTPException(status_code=404, detail=f'Setting "{key}" not found')
    setting.value = payload.value
    db.commit()
    db.refresh(setting)
    return setting
