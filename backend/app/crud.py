import json
from datetime import date

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session, joinedload

from . import models, schemas


def create_ingredient_master(
    db: Session, payload: schemas.IngredientMasterCreate
) -> models.IngredientMaster:
    item = models.IngredientMaster(
        name=payload.name,
        name_reading=payload.name_reading,
        aliases=payload.aliases,
        category_id=payload.category_id,
        default_storage_location=payload.default_storage_location,
        default_expiry_days=payload.default_expiry_days,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_ingredient_masters(
    db: Session, include_inactive: bool = False, name: str | None = None
):
    stmt = (
        select(models.IngredientMaster)
        .options(joinedload(models.IngredientMaster.category_ref))
        .order_by(models.IngredientMaster.name.asc())
    )
    if not include_inactive:
        stmt = stmt.where(models.IngredientMaster.is_active.is_(True))
    if name:
        stmt = stmt.where(
            or_(
                models.IngredientMaster.name.contains(name),
                models.IngredientMaster.name_reading.contains(name),
                models.IngredientMaster.aliases.contains(name),
            )
        )
    return db.scalars(stmt).all()


def get_ingredient_master(db: Session, master_id: int):
    stmt = (
        select(models.IngredientMaster)
        .where(models.IngredientMaster.id == master_id)
        .options(joinedload(models.IngredientMaster.category_ref))
    )
    return db.scalar(stmt)


def update_ingredient_master(
    db: Session, current: models.IngredientMaster, payload: schemas.IngredientMasterUpdate
):
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(current, key, value)
    db.commit()
    db.refresh(current)
    return current


def create_category(db: Session, payload: schemas.CategoryCreate) -> models.Category:
    item = models.Category(name=payload.name, sort_order=payload.sort_order)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_categories(db: Session, include_inactive: bool = False):
    stmt = select(models.Category).order_by(models.Category.sort_order.asc(), models.Category.name.asc())
    if not include_inactive:
        stmt = stmt.where(models.Category.is_active.is_(True))
    return db.scalars(stmt).all()


def get_category(db: Session, category_id: int):
    return db.get(models.Category, category_id)


def update_category(db: Session, current: models.Category, payload: schemas.CategoryUpdate):
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(current, key, value)
    db.commit()
    db.refresh(current)
    return current


def create_storage_location(
    db: Session, payload: schemas.StorageLocationCreate
) -> models.StorageLocation:
    item = models.StorageLocation(name=payload.name, sort_order=payload.sort_order)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_storage_locations(db: Session, include_inactive: bool = False):
    stmt = select(models.StorageLocation).order_by(
        models.StorageLocation.sort_order.asc(), models.StorageLocation.name.asc()
    )
    if not include_inactive:
        stmt = stmt.where(models.StorageLocation.is_active.is_(True))
    return db.scalars(stmt).all()


def get_storage_location(db: Session, storage_location_id: int):
    return db.get(models.StorageLocation, storage_location_id)


def get_storage_location_by_name(db: Session, name: str):
    stmt = select(models.StorageLocation).where(models.StorageLocation.name == name)
    return db.scalar(stmt)


def update_storage_location(
    db: Session, current: models.StorageLocation, payload: schemas.StorageLocationUpdate
):
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(current, key, value)
    db.commit()
    db.refresh(current)
    return current


def create_ingredient(db: Session, payload: schemas.IngredientCreate) -> models.Ingredient:
    item = models.Ingredient(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_ingredient(db: Session, ingredient_id: int):
    stmt = (
        select(models.Ingredient)
        .where(models.Ingredient.id == ingredient_id)
        .options(joinedload(models.Ingredient.master))
    )
    return db.scalar(stmt)


def update_ingredient(
    db: Session, current: models.Ingredient, payload: schemas.IngredientUpdate
):
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(current, key, value)
    db.commit()
    db.refresh(current)
    return current


def delete_ingredient(db: Session, current: models.Ingredient):
    db.delete(current)
    db.commit()


def append_ingredient_event(
    db: Session, ingredient_id: int | None, event_type: str, payload: dict | None = None
) -> models.IngredientEvent:
    row = models.IngredientEvent(
        ingredient_id=ingredient_id,
        event_type=event_type,
        payload=json.dumps(payload, ensure_ascii=False, default=str) if payload else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_ingredient_events(db: Session, ingredient_id: int):
    stmt = (
        select(models.IngredientEvent)
        .where(models.IngredientEvent.ingredient_id == ingredient_id)
        .order_by(models.IngredientEvent.created_at.desc())
    )
    return db.scalars(stmt).all()


def search_ingredients(
    db: Session,
    *,
    name: str | None = None,
    storage_location: str | None = None,
    quantity_status: schemas.QuantityStatus | None = None,
    expiry_before: date | None = None,
    has_opened_date: bool | None = None,
):
    stmt: Select[tuple[models.Ingredient]] = (
        select(models.Ingredient)
        .join(models.IngredientMaster, models.Ingredient.master)
        .options(joinedload(models.Ingredient.master))
        .order_by(models.Ingredient.updated_at.desc())
    )
    if name:
        stmt = stmt.where(
            or_(
                models.IngredientMaster.name.contains(name),
                models.IngredientMaster.name_reading.contains(name),
                models.IngredientMaster.aliases.contains(name),
            )
        )
    if storage_location:
        stmt = stmt.where(models.Ingredient.storage_location == storage_location)
    if quantity_status:
        stmt = stmt.where(models.Ingredient.quantity_status == quantity_status)
    if expiry_before:
        stmt = stmt.where(models.Ingredient.expiry_date.is_not(None))
        stmt = stmt.where(models.Ingredient.expiry_date <= expiry_before)
    if has_opened_date is True:
        stmt = stmt.where(models.Ingredient.opened_date.is_not(None))
    if has_opened_date is False:
        stmt = stmt.where(models.Ingredient.opened_date.is_(None))
    return db.scalars(stmt).all()
