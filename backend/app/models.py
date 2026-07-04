"""
SQLAlchemy models.

Tables are prefixed sfc_ (Shopfitting Costing) as defense-in-depth against
ever landing on a shared database with another app by accident - the same
mitigation used in Engineering-Management-App, even though this app is
meant to get its own dedicated Postgres database from day one.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum, Boolean, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Typology(str, enum.Enum):
    horizontal_box = "horizontal_box"
    vertical_box = "vertical_box"
    flat_framework = "flat_framework"
    area_cladding = "area_cladding"
    framing_lines = "framing_lines"


class User(Base):
    __tablename__ = "sfc_users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class Material(Base):
    __tablename__ = "sfc_materials"

    id = Column(Integer, primary_key=True)
    category = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    supplied_as = Column(String(50), nullable=True)  # Sheet, Unit, Roll, Litre, m2...
    length_mm = Column(Float, nullable=True)
    width_mm = Column(Float, nullable=True)
    thickness_mm = Column(Float, nullable=True)
    cost = Column(Float, nullable=False)  # ZAR, excl VAT
    unit = Column(String(20), nullable=False, default="per_m2")  # per_m2, per_lm, each
    waste_pct = Column(Float, nullable=True)  # e.g. 0.15 for 15%, overrides typology default when set
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Setting(Base):
    """
    Small key/value store for business-wide numbers that should be editable
    without a code change - the same "update without touching the app" rule
    applied to Materials. Seeded with labour_rate (350.0, from the Master
    Price List) and kerf_mm (saw blade allowance, default 3.0).
    """
    __tablename__ = "sfc_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Float, nullable=False)
    description = Column(String(500), nullable=True)


class Project(Base):
    __tablename__ = "sfc_projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    project_number = Column(String(100), nullable=True)
    sponsor = Column(String(255), nullable=True)
    client_info = Column(Text, nullable=True)
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    special_instructions = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("sfc_users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    items = relationship("Item", back_populates="project", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "sfc_items"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("sfc_projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    drawing_filename = Column(String(500), nullable=True)  # reference/record only, v1
    fixture_category = Column(String(50), nullable=True)  # "modular" / "standard_joinery" / "bespoke_premium" - reference label only
    labour_multiplier = Column(Float, nullable=False, default=1.0)  # labour_cost = material_cost x this, per-item
    created_at = Column(DateTime(timezone=True), default=utcnow)

    project = relationship("Project", back_populates="items")
    components = relationship("Component", back_populates="item", cascade="all, delete-orphan")


class Component(Base):
    """
    One typology-priced sub-element of an Item. A simple item (a single desk)
    has one Component; a multi-typology item (counter + glass display case)
    has several, per the "LEGO rule" agreed in the build notes.
    """
    __tablename__ = "sfc_components"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("sfc_items.id"), nullable=False)
    typology = Column(Enum(Typology), nullable=False)
    name = Column(String(255), nullable=True)  # optional label, e.g. "Base counter"
    inputs = Column(JSON, nullable=False)  # raw typology inputs as submitted
    derived_panels = Column(JSON, nullable=False)  # list of {name, width_mm, length_mm, qty}
    board_area_m2 = Column(Float, nullable=True)  # for sheet-based typologies
    linear_m = Column(Float, nullable=True)  # for linear-stock typologies
    labour_hours = Column(Float, nullable=False)
    material_cost = Column(Float, nullable=False)
    labour_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    item = relationship("Item", back_populates="components")
