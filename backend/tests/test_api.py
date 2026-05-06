from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

client = TestClient(app)


def setup_module():
    # conftest で DATABASE_URL がインメモリに固定されている前提でリセットする。
    # 本番ファイルを指している場合はここを実行してはいけない（データ全消去になる）。
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
        json={
            "name": "卵",
            "category_id": category_id,
            "default_storage_location": "冷蔵",
            "default_expiry_days": 5,
        },
    )
    assert master.status_code == 201
    master_id = master.json()["id"]
    assert master.json()["default_storage_location"] == "冷蔵"
    assert master.json()["default_expiry_days"] == 5

    listed_master = client.get("/ingredient-masters")
    assert listed_master.status_code == 200
    assert len(listed_master.json()) == 1
    assert listed_master.json()[0]["default_storage_location"] == "冷蔵"
    assert listed_master.json()[0]["default_expiry_days"] == 5

    filtered_masters = client.get("/ingredient-masters", params={"name": "卵"})
    assert filtered_masters.status_code == 200
    assert len(filtered_masters.json()) == 1
    assert filtered_masters.json()[0]["name"] == "卵"

    no_match = client.get("/ingredient-masters", params={"name": "存在しない"})
    assert no_match.status_code == 200
    assert len(no_match.json()) == 0

    patch_meta = client.patch(
        f"/ingredient-masters/{master_id}",
        json={"name_reading": "たまご", "aliases": "玉子\negg", "default_expiry_days": None},
    )
    assert patch_meta.status_code == 200
    assert patch_meta.json()["name_reading"] == "たまご"
    assert "玉子" in patch_meta.json()["aliases"]
    assert patch_meta.json()["default_expiry_days"] is None

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
            "quantity_status": "購入必要",
            "storage_location": "冷蔵",
            "note": "テストデータ",
        },
    )
    assert created.status_code == 201
    ingredient_id = created.json()["id"]
    assert created.json()["purchased_date"] is None

    filtered = client.get("/ingredients", params={"name": "卵", "storage_location": "冷蔵"})
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    by_ingredient_alias = client.get("/ingredients", params={"name": "玉子"})
    assert by_ingredient_alias.status_code == 200
    assert len(by_ingredient_alias.json()) == 1

    updated = client.patch(f"/ingredients/{ingredient_id}", json={"quantity_status": "少ない"})
    assert updated.status_code == 200
    assert updated.json()["quantity_status"] == "少ない"
    assert updated.json()["purchased_date"] is not None

    purchase = client.get("/ingredients", params={"quantity_status": "少ない"})
    assert purchase.status_code == 200
    assert len(purchase.json()) == 1

    deleted = client.delete(f"/ingredients/{ingredient_id}")
    assert deleted.status_code == 204

    events = client.get(f"/ingredients/{ingredient_id}/events")
    assert events.status_code == 200
    evs = events.json()
    assert len(evs) == 3
    types_in_order = [e["event_type"] for e in evs]
    assert types_in_order == ["deleted", "updated", "created"]


def test_expiry_auto_from_opened_date():
    loc = client.post("/storage-locations", json={"name": "冷蔵オープン後", "sort_order": 1})
    assert loc.status_code == 201
    category = client.post("/categories", json={"name": "テスト乳", "sort_order": 1})
    assert category.status_code == 201
    category_id = category.json()["id"]
    master = client.post(
        "/ingredient-masters",
        json={
            "name": "開封テスト品",
            "category_id": category_id,
            "default_storage_location": "冷蔵オープン後",
            "default_expiry_days": 3,
        },
    )
    assert master.status_code == 201
    master_id = master.json()["id"]

    opened = date(2026, 5, 1)
    created = client.post(
        "/ingredients",
        json={
            "ingredient_master_id": master_id,
            "quantity_status": "少ない",
            "storage_location": "冷蔵オープン後",
            "purchased_date": "2026-04-20",
            "opened_date": opened.isoformat(),
            "expiry_date": None,
            "note": None,
        },
    )
    assert created.status_code == 201
    assert created.json()["expiry_date"] == (opened + timedelta(days=3)).isoformat()

    ingredient_id = created.json()["id"]
    new_opened = date(2026, 5, 10)
    stale_expiry = (opened + timedelta(days=3)).isoformat()
    patched = client.patch(
        f"/ingredients/{ingredient_id}",
        json={
            "ingredient_master_id": master_id,
            "quantity_status": "少ない",
            "storage_location": "冷蔵オープン後",
            "purchased_date": "2026-04-20",
            "opened_date": new_opened.isoformat(),
            "expiry_date": stale_expiry,
            "note": None,
        },
    )
    assert patched.status_code == 200
    assert patched.json()["expiry_date"] == (new_opened + timedelta(days=3)).isoformat()

    user_expiry = date(2026, 12, 31)
    patched2 = client.patch(
        f"/ingredients/{ingredient_id}",
        json={
            "ingredient_master_id": master_id,
            "quantity_status": "少ない",
            "storage_location": "冷蔵オープン後",
            "purchased_date": "2026-04-20",
            "opened_date": date(2026, 5, 15).isoformat(),
            "expiry_date": user_expiry.isoformat(),
            "note": None,
        },
    )
    assert patched2.status_code == 200
    assert patched2.json()["expiry_date"] == user_expiry.isoformat()
