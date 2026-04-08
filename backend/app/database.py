import os

from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./food_manager.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_schema_migrations():
    with engine.begin() as conn:
        inspector = inspect(conn)
        tables = inspector.get_table_names()
        if "ingredient_masters" not in tables:
            return

        master_cols = {col["name"] for col in inspector.get_columns("ingredient_masters")}
        if "category_id" not in master_cols:
            conn.execute(text("ALTER TABLE ingredient_masters ADD COLUMN category_id INTEGER"))

        if "categories" in inspector.get_table_names():
            category_count = conn.execute(text("SELECT COUNT(*) FROM categories")).scalar_one()
            if category_count == 0:
                for idx, name in enumerate(["野菜", "肉", "魚", "乳製品", "調味料", "飲料", "冷凍食品", "その他"]):
                    conn.execute(
                        text(
                            "INSERT INTO categories (name, is_active, sort_order, created_at, updated_at) "
                            "VALUES (:name, 1, :sort_order, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                        ),
                        {"name": name, "sort_order": idx},
                    )

        if "category" in master_cols and "categories" in inspector.get_table_names():
            rows = conn.execute(
                text(
                    "SELECT DISTINCT category FROM ingredient_masters "
                    "WHERE category IS NOT NULL AND category <> ''"
                )
            ).fetchall()
            for row in rows:
                cat_name = row[0]
                existing = conn.execute(
                    text("SELECT id FROM categories WHERE name = :name"),
                    {"name": cat_name},
                ).first()
                if existing is None:
                    conn.execute(
                        text(
                            "INSERT INTO categories (name, is_active, sort_order, created_at, updated_at) "
                            "VALUES (:name, 1, 999, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                        ),
                        {"name": cat_name},
                    )
                conn.execute(
                    text(
                        "UPDATE ingredient_masters "
                        "SET category_id = (SELECT id FROM categories WHERE name = :name) "
                        "WHERE category = :name AND (category_id IS NULL OR category_id = 0)"
                    ),
                    {"name": cat_name},
                )
