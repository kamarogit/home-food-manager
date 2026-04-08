from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from . import models, schemas


def create_ingredient_master(
    db: Session, payload: schemas.IngredientMasterCreate
) -> models.IngredientMaster:
    item = models.IngredientMaster(name=payload.name, category_id=payload.category_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_ingredient_masters(db: Session, include_inactive: bool = False):
    stmt = (
        select(models.IngredientMaster)
        .options(joinedload(models.IngredientMaster.category_ref))
        .order_by(models.IngredientMaster.name.asc())
    )
    if not include_inactive:
        stmt = stmt.where(models.IngredientMaster.is_active.is_(True))
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
        stmt = stmt.where(models.IngredientMaster.name.contains(name))
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
