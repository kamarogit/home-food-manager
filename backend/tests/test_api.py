from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_master_and_ingredient_flow():
    location = client.post("/storage-locations", json={"name": "冷蔵", "sort_order": 1})
    assert location.status_code == 201

    category = client.post("/categories", json={"name": "乳製品", "sort_order": 1})
    assert category.status_code == 201
    category_id = category.json()["id"]

    master = client.post(
        "/ingredient-masters",
        json={"name": "卵", "category_id": category_id, "default_storage_location": "冷蔵"},
    )
    assert master.status_code == 201
    master_id = master.json()["id"]
    assert master.json()["default_storage_location"] == "冷蔵"

    listed_master = client.get("/ingredient-masters")
    assert listed_master.status_code == 200
    assert len(listed_master.json()) == 1
    assert listed_master.json()[0]["default_storage_location"] == "冷蔵"

    filtered_masters = client.get("/ingredient-masters", params={"name": "卵"})
    assert filtered_masters.status_code == 200
    assert len(filtered_masters.json()) == 1
    assert filtered_masters.json()[0]["name"] == "卵"

    no_match = client.get("/ingredient-masters", params={"name": "存在しない"})
    assert no_match.status_code == 200
    assert len(no_match.json()) == 0

    patch_meta = client.patch(
        f"/ingredient-masters/{master_id}",
        json={"name_reading": "たまご", "aliases": "玉子\negg"},
    )
    assert patch_meta.status_code == 200
    assert patch_meta.json()["name_reading"] == "たまご"
    assert "玉子" in patch_meta.json()["aliases"]

    by_reading = client.get("/ingredient-masters", params={"name": "たまご"})
    assert by_reading.status_code == 200
    assert len(by_reading.json()) == 1

    by_alias = client.get("/ingredient-masters", params={"name": "玉子"})
    assert by_alias.status_code == 200
    assert len(by_alias.json()) == 1

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

    by_ingredient_alias = client.get("/ingredients", params={"name": "玉子"})
    assert by_ingredient_alias.status_code == 200
    assert len(by_ingredient_alias.json()) == 1

    updated = client.patch(f"/ingredients/{ingredient_id}", json={"quantity_status": "購入必要"})
    assert updated.status_code == 200
    assert updated.json()["quantity_status"] == "購入必要"

    purchase = client.get("/ingredients", params={"quantity_status": "購入必要"})
    assert purchase.status_code == 200
    assert len(purchase.json()) == 1

    deleted = client.delete(f"/ingredients/{ingredient_id}")
    assert deleted.status_code == 204
