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
