from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


class StorageLocationBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class StorageLocationCreate(StorageLocationBase):
    sort_order: int = 0


class StorageLocationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None
    sort_order: int | None = None


class StorageLocationRead(StorageLocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class IngredientMasterBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    name_reading: str | None = Field(default=None, max_length=255)
    aliases: str | None = Field(default=None, max_length=8192)
    category_id: int | None = None
    default_storage_location: str | None = Field(default=None, max_length=100)


class IngredientMasterCreate(IngredientMasterBase):
    @field_validator("name_reading", "aliases", mode="before")
    @classmethod
    def _optional_text_blanks(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


class IngredientMasterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    name_reading: str | None = Field(default=None, max_length=255)
    aliases: str | None = Field(default=None, max_length=8192)
    category_id: int | None = None
    default_storage_location: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None

    @field_validator("name_reading", "aliases", mode="before")
    @classmethod
    def _optional_text_blanks(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


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
