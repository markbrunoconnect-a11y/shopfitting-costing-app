from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr

from app.models import Typology


# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Materials ---
class MaterialCreate(BaseModel):
    category: str
    name: str
    supplied_as: Optional[str] = None
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    thickness_mm: Optional[float] = None
    cost: float
    unit: str = "per_m2"
    waste_pct: Optional[float] = None


class MaterialUpdate(BaseModel):
    category: Optional[str] = None
    name: Optional[str] = None
    supplied_as: Optional[str] = None
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    thickness_mm: Optional[float] = None
    cost: Optional[float] = None
    unit: Optional[str] = None
    waste_pct: Optional[float] = None
    is_active: Optional[bool] = None


class MaterialOut(MaterialCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


# --- Projects ---
class ProjectCreate(BaseModel):
    name: str
    project_number: Optional[str] = None
    sponsor: Optional[str] = None
    client_info: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    special_instructions: Optional[str] = None


class ProjectOut(ProjectCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Items / Components ---
class ComponentCreate(BaseModel):
    typology: Typology
    name: Optional[str] = None
    inputs: dict[str, Any]  # typology-specific fields, validated inside the typology engine


class ItemCreate(BaseModel):
    name: str
    quantity: int = 1
    components: list[ComponentCreate]


class ComponentOut(BaseModel):
    id: int
    typology: Typology
    name: Optional[str]
    inputs: dict[str, Any]
    derived_panels: list[dict[str, Any]]
    board_area_m2: Optional[float]
    linear_m: Optional[float]
    labour_hours: float
    material_cost: float
    labour_cost: float
    total_cost: float

    class Config:
        from_attributes = True


class ItemOut(BaseModel):
    id: int
    project_id: int
    name: str
    quantity: int
    components: list[ComponentOut]

    class Config:
        from_attributes = True
