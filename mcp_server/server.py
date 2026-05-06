from typing import Any
import os
from urllib.parse import quote

import httpx
from fastmcp import FastMCP

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
mcp = FastMCP("home-food-manager")


def _request(method: str, path: str, json: dict[str, Any] | None = None):
    with httpx.Client(timeout=10.0) as client:
        response = client.request(method, f"{API_BASE}{path}", json=json)
        response.raise_for_status()
        if response.status_code == 204:
            return {"ok": True}
        return response.json()


@mcp.tool()
def list_ingredients() -> list[dict[str, Any]]:
    return _request("GET", "/ingredients")


@mcp.tool()
def list_ingredient_masters(
    include_inactive: bool = False,
    name: str | None = None,
) -> list[dict[str, Any]]:
    query = []
    if include_inactive:
        query.append("include_inactive=true")
    if name:
        query.append(f"name={quote(name, safe='')}")
    suffix = f"?{'&'.join(query)}" if query else ""
    return _request("GET", f"/ingredient-masters{suffix}")


@mcp.tool()
def create_ingredient_master(
    name: str,
    category_id: int | None = None,
    default_storage_location: str | None = None,
    name_reading: str | None = None,
    aliases: str | None = None,
) -> dict[str, Any]:
    return _request(
        "POST",
        "/ingredient-masters",
        {
            "name": name,
            "category_id": category_id,
            "default_storage_location": default_storage_location,
            "name_reading": name_reading,
            "aliases": aliases,
        },
    )


@mcp.tool()
def update_ingredient_master(
    master_id: int,
    name: str | None = None,
    name_reading: str | None = None,
    aliases: str | None = None,
    category_id: int | None = None,
    default_storage_location: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if name is not None:
        payload["name"] = name
    if name_reading is not None:
        payload["name_reading"] = name_reading
    if aliases is not None:
        payload["aliases"] = aliases
    if category_id is not None:
        payload["category_id"] = category_id
    if default_storage_location is not None:
        payload["default_storage_location"] = default_storage_location
    if is_active is not None:
        payload["is_active"] = is_active
    return _request("PATCH", f"/ingredient-masters/{master_id}", payload)


@mcp.tool()
def list_categories(include_inactive: bool = False) -> list[dict[str, Any]]:
    suffix = "?include_inactive=true" if include_inactive else ""
    return _request("GET", f"/categories{suffix}")


@mcp.tool()
def list_storage_locations(include_inactive: bool = False) -> list[dict[str, Any]]:
    suffix = "?include_inactive=true" if include_inactive else ""
    return _request("GET", f"/storage-locations{suffix}")


@mcp.tool()
def search_ingredients(
    name: str | None = None,
    storage_location: str | None = None,
    quantity_status: str | None = None,
    expiry_before: str | None = None,
) -> list[dict[str, Any]]:
    query = []
    if name:
        query.append(f"name={name}")
    if storage_location:
        query.append(f"storage_location={storage_location}")
    if quantity_status:
        query.append(f"quantity_status={quantity_status}")
    if expiry_before:
        query.append(f"expiry_before={expiry_before}")
    suffix = f"?{'&'.join(query)}" if query else ""
    return _request("GET", f"/ingredients{suffix}")


@mcp.tool()
def add_ingredient(
    ingredient_master_id: int,
    quantity_status: str,
    storage_location: str = "未設定",
    expiry_date: str | None = None,
    opened_date: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    return _request(
        "POST",
        "/ingredients",
        {
            "ingredient_master_id": ingredient_master_id,
            "quantity_status": quantity_status,
            "storage_location": storage_location,
            "expiry_date": expiry_date,
            "opened_date": opened_date,
            "note": note,
        },
    )


@mcp.tool()
def update_ingredient(
    ingredient_id: int,
    quantity_status: str | None = None,
    storage_location: str | None = None,
    expiry_date: str | None = None,
    opened_date: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    payload = {
        "quantity_status": quantity_status,
        "storage_location": storage_location,
        "expiry_date": expiry_date,
        "opened_date": opened_date,
        "note": note,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return _request("PATCH", f"/ingredients/{ingredient_id}", payload)


@mcp.tool()
def delete_ingredient(ingredient_id: int) -> dict[str, Any]:
    return _request("DELETE", f"/ingredients/{ingredient_id}")


@mcp.tool()
def list_purchase_needed_ingredients() -> list[dict[str, Any]]:
    return _request("GET", "/ingredients?quantity_status=購入必要")


if __name__ == "__main__":
    mcp.run()
