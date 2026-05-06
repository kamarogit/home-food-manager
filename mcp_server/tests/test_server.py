import server


def test_list_purchase_needed_ingredients(monkeypatch):
    def fake_request(method, path, json=None):
        assert method == "GET"
        assert path == "/ingredients?quantity_status=購入必要"
        return [{"id": 1, "ingredient_name": "牛乳"}]

    monkeypatch.setattr(server, "_request", fake_request)
    result = server.list_purchase_needed_ingredients()
    assert len(result) == 1


def test_add_ingredient_calls_api(monkeypatch):
    captured = {}

    def fake_request(method, path, json=None):
        captured["method"] = method
        captured["path"] = path
        captured["json"] = json
        return {"id": 10}

    monkeypatch.setattr(server, "_request", fake_request)
    result = server.add_ingredient(1, "少ない", storage_location="冷蔵")

    assert result["id"] == 10
    assert captured["method"] == "POST"
    assert captured["path"] == "/ingredients"
    assert captured["json"]["quantity_status"] == "少ない"


def test_list_ingredient_masters_builds_query(monkeypatch):
    captured = {}

    def fake_request(method, path, json=None):
        captured["path"] = path
        return []

    monkeypatch.setattr(server, "_request", fake_request)
    server.list_ingredient_masters(include_inactive=True, name="牛乳")
    assert "include_inactive=true" in captured["path"]
    assert "name=" in captured["path"]


def test_create_ingredient_master_calls_api(monkeypatch):
    captured = {}

    def fake_request(method, path, json=None):
        captured["method"] = method
        captured["path"] = path
        captured["json"] = json
        return {"id": 5, "name": "豆腐"}

    monkeypatch.setattr(server, "_request", fake_request)
    result = server.create_ingredient_master(
        "豆腐",
        category_id=2,
        default_storage_location="冷蔵",
        name_reading="とうふ",
        aliases="豆富\nソイビーンカード",
    )

    assert result["id"] == 5
    assert captured["method"] == "POST"
    assert captured["path"] == "/ingredient-masters"
    assert captured["json"] == {
        "name": "豆腐",
        "category_id": 2,
        "default_storage_location": "冷蔵",
        "name_reading": "とうふ",
        "aliases": "豆富\nソイビーンカード",
    }


def test_update_ingredient_master_calls_api(monkeypatch):
    captured = {}

    def fake_request(method, path, json=None):
        captured["method"] = method
        captured["path"] = path
        captured["json"] = json
        return {"id": 1}

    monkeypatch.setattr(server, "_request", fake_request)
    server.update_ingredient_master(1, name_reading="たまご", is_active=False)

    assert captured["method"] == "PATCH"
    assert captured["path"] == "/ingredient-masters/1"
    assert captured["json"] == {"name_reading": "たまご", "is_active": False}


def test_list_categories(monkeypatch):
    def fake_request(method, path, json=None):
        assert path == "/categories"
        return [{"id": 1}]

    monkeypatch.setattr(server, "_request", fake_request)
    assert server.list_categories() == [{"id": 1}]


def test_list_storage_locations_inactive(monkeypatch):
    def fake_request(method, path, json=None):
        assert path == "/storage-locations?include_inactive=true"
        return []

    monkeypatch.setattr(server, "_request", fake_request)
    assert server.list_storage_locations(include_inactive=True) == []
