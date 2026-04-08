from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_master_and_ingredient_flow():
    category = client.post("/categories", json={"name": "乳製品", "sort_order": 1})
    assert category.status_code == 201
    category_id = category.json()["id"]

    master = client.post("/ingredient-masters", json={"name": "卵", "category_id": category_id})
    assert master.status_code == 201
    master_id = master.json()["id"]

    listed_master = client.get("/ingredient-masters")
    assert listed_master.status_code == 200
    assert len(listed_master.json()) == 1

    created = client.post(
        "/ingredients",
        json={
            "ingredient_master_id": master_id,
            "quantity_status": "少ない",
            "storage_location": "冷蔵",
            "note": "テストデータ",
        },
    )
    assert created.status_code == 201
    ingredient_id = created.json()["id"]

    filtered = client.get("/ingredients", params={"name": "卵", "storage_location": "冷蔵"})
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    updated = client.patch(f"/ingredients/{ingredient_id}", json={"quantity_status": "購入必要"})
    assert updated.status_code == 200
    assert updated.json()["quantity_status"] == "購入必要"

    purchase = client.get("/ingredients", params={"quantity_status": "購入必要"})
    assert purchase.status_code == 200
    assert len(purchase.json()) == 1

    deleted = client.delete(f"/ingredients/{ingredient_id}")
    assert deleted.status_code == 204
