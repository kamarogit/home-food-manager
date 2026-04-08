from datetime import date
import os

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import Base, engine, get_db, run_schema_migrations

app = FastAPI(title="home-food-manager API")

raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
cors_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
run_schema_migrations()


def to_ingredient_read(item: models.Ingredient) -> schemas.IngredientRead:
    return schemas.IngredientRead(
        id=item.id,
        ingredient_master_id=item.ingredient_master_id,
        ingredient_name=item.master.name,
        ingredient_category=item.master.category_ref.name if item.master.category_ref else item.master.category,
        quantity_status=item.quantity_status,
        storage_location=item.storage_location,
        expiry_date=item.expiry_date,
        opened_date=item.opened_date,
        note=item.note,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def to_ingredient_master_read(item: models.IngredientMaster) -> schemas.IngredientMasterRead:
    return schemas.IngredientMasterRead(
        id=item.id,
        name=item.name,
        category_id=item.category_id,
        category_name=item.category_ref.name if item.category_ref else item.category,
        is_active=item.is_active,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@app.post(
    "/ingredient-masters",
    response_model=schemas.IngredientMasterRead,
    status_code=status.HTTP_201_CREATED,
)
def create_ingredient_master(
    payload: schemas.IngredientMasterCreate, db: Session = Depends(get_db)
):
    if payload.category_id is not None:
        category = crud.get_category(db, payload.category_id)
        if not category or not category.is_active:
            raise HTTPException(status_code=400, detail="有効なカテゴリを指定してください。")
    try:
        return to_ingredient_master_read(crud.create_ingredient_master(db, payload))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="食材マスタ名が重複しています。")


@app.get("/ingredient-masters", response_model=list[schemas.IngredientMasterRead])
def list_ingredient_masters(
    include_inactive: bool = Query(default=False), db: Session = Depends(get_db)
):
    return [
        to_ingredient_master_read(item)
        for item in crud.list_ingredient_masters(db, include_inactive=include_inactive)
    ]


@app.patch("/ingredient-masters/{master_id}", response_model=schemas.IngredientMasterRead)
def patch_ingredient_master(
    master_id: int, payload: schemas.IngredientMasterUpdate, db: Session = Depends(get_db)
):
    current = crud.get_ingredient_master(db, master_id)
    if not current:
        raise HTTPException(status_code=404, detail="食材マスタが見つかりません。")
    if payload.category_id is not None:
        category = crud.get_category(db, payload.category_id)
        if not category or not category.is_active:
            raise HTTPException(status_code=400, detail="有効なカテゴリを指定してください。")
    try:
        return to_ingredient_master_read(crud.update_ingredient_master(db, current, payload))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="食材マスタ名が重複しています。")


@app.post("/categories", response_model=schemas.CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_category(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="カテゴリ名が重複しています。")


@app.get("/categories", response_model=list[schemas.CategoryRead])
def list_categories(
    include_inactive: bool = Query(default=False), db: Session = Depends(get_db)
):
    return crud.list_categories(db, include_inactive=include_inactive)


@app.patch("/categories/{category_id}", response_model=schemas.CategoryRead)
def patch_category(
    category_id: int, payload: schemas.CategoryUpdate, db: Session = Depends(get_db)
):
    current = crud.get_category(db, category_id)
    if not current:
        raise HTTPException(status_code=404, detail="カテゴリが見つかりません。")
    try:
        return crud.update_category(db, current, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="カテゴリ名が重複しています。")


@app.post("/ingredients", response_model=schemas.IngredientRead, status_code=status.HTTP_201_CREATED)
def create_ingredient(payload: schemas.IngredientCreate, db: Session = Depends(get_db)):
    master = crud.get_ingredient_master(db, payload.ingredient_master_id)
    if not master or not master.is_active:
        raise HTTPException(status_code=400, detail="有効な食材マスタを指定してください。")
    item = crud.create_ingredient(db, payload)
    item = crud.get_ingredient(db, item.id)
    if item is None:
        raise HTTPException(status_code=500, detail="在庫取得に失敗しました。")
    return to_ingredient_read(item)


@app.get("/ingredients", response_model=list[schemas.IngredientRead])
def list_ingredients(
    name: str | None = Query(default=None),
    storage_location: str | None = Query(default=None),
    quantity_status: schemas.QuantityStatus | None = Query(default=None),
    expiry_before: date | None = Query(default=None),
    has_opened_date: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    items = crud.search_ingredients(
        db,
        name=name,
        storage_location=storage_location,
        quantity_status=quantity_status,
        expiry_before=expiry_before,
        has_opened_date=has_opened_date,
    )
    return [to_ingredient_read(item) for item in items]


@app.get("/ingredients/{ingredient_id}", response_model=schemas.IngredientRead)
def get_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    item = crud.get_ingredient(db, ingredient_id)
    if not item:
        raise HTTPException(status_code=404, detail="在庫が見つかりません。")
    return to_ingredient_read(item)


@app.patch("/ingredients/{ingredient_id}", response_model=schemas.IngredientRead)
def patch_ingredient(
    ingredient_id: int, payload: schemas.IngredientUpdate, db: Session = Depends(get_db)
):
    current = crud.get_ingredient(db, ingredient_id)
    if not current:
        raise HTTPException(status_code=404, detail="在庫が見つかりません。")
    if payload.ingredient_master_id is not None:
        master = crud.get_ingredient_master(db, payload.ingredient_master_id)
        if not master or not master.is_active:
            raise HTTPException(status_code=400, detail="有効な食材マスタを指定してください。")
    item = crud.update_ingredient(db, current, payload)
    item = crud.get_ingredient(db, item.id)
    if item is None:
        raise HTTPException(status_code=500, detail="在庫取得に失敗しました。")
    return to_ingredient_read(item)


@app.delete("/ingredients/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    current = crud.get_ingredient(db, ingredient_id)
    if not current:
        raise HTTPException(status_code=404, detail="在庫が見つかりません。")
    crud.delete_ingredient(db, current)
