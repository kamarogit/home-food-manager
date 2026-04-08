from typing import Any
import os

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
