from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class IngredientMaster(Base):
    __tablename__ = "ingredient_masters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    ingredients: Mapped[list["Ingredient"]] = relationship(back_populates="master")
    category_ref: Mapped["Category | None"] = relationship(back_populates="ingredient_masters")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    ingredient_masters: Mapped[list[IngredientMaster]] = relationship(back_populates="category_ref")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ingredient_master_id: Mapped[int] = mapped_column(
        ForeignKey("ingredient_masters.id"), nullable=False, index=True
    )
    quantity_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    storage_location: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    expiry_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    opened_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    master: Mapped[IngredientMaster] = relationship(back_populates="ingredients")
