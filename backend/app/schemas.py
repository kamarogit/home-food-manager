from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

QuantityStatus = Literal["多い", "少ない", "購入必要"]


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class CategoryCreate(CategoryBase):
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None
    sort_order: int | None = None


class CategoryRead(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class IngredientMasterBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category_id: int | None = None


class IngredientMasterCreate(IngredientMasterBase):
    pass


class IngredientMasterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = None
    is_active: bool | None = None


class IngredientMasterRead(IngredientMasterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category_name: str | None = None


class IngredientBase(BaseModel):
    ingredient_master_id: int
    quantity_status: QuantityStatus
    storage_location: str | None = None
    expiry_date: date | None = None
    opened_date: date | None = None
    note: str | None = None


class IngredientCreate(IngredientBase):
    pass


class IngredientUpdate(BaseModel):
    ingredient_master_id: int | None = None
    quantity_status: QuantityStatus | None = None
    storage_location: str | None = None
    expiry_date: date | None = None
    opened_date: date | None = None
    note: str | None = None


class IngredientRead(IngredientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    ingredient_name: str
    ingredient_category: str | None = None
