"""Модуль «Склады» — остатки, склады, поставки, пункты приёмки."""

from __future__ import annotations

from typing import Any

from mcp_wb.src.wb_client import WBClient  # noqa: E402


async def get_warehouses(client: WBClient) -> list[dict[str, Any]]:
    """Получить список складов продавца."""
    return await client.get("marketplace", "/api/v3/warehouses")


async def get_warehouse_stocks(
    client: WBClient, warehouse_id: int
) -> list[dict[str, Any]]:
    """Получить остатки по конкретному складу."""
    return await client.get(
        "marketplace", f"/api/v3/stocks/{warehouse_id}"
    )


async def get_supplies(client: WBClient) -> list[dict[str, Any]]:
    """Получить список поставок."""
    return await client.get("marketplace", "/api/v3/supplies")


async def get_supply_detail(
    client: WBClient, supply_id: str
) -> dict[str, Any]:
    """Получить детали конкретной поставки."""
    return await client.get("marketplace", f"/api/v3/supplies/{supply_id}")


async def get_offices(client: WBClient) -> list[dict[str, Any]]:
    """Получить список пунктов приёмки WB."""
    return await client.get("marketplace", "/api/v3/offices")


# Реестр инструментов модуля
WAREHOUSE_TOOLS = [
    {
        "name": "wb_get_warehouses",
        "module": "warehouses",
        "description": "Список складов продавца",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "wb_get_warehouse_stocks",
        "module": "warehouses",
        "description": "Остатки по конкретному складу WB",
        "parameters": {
            "type": "object",
            "properties": {
                "warehouse_id": {"type": "integer", "description": "ID склада"},
            },
            "required": ["warehouse_id"],
        },
    },
    {
        "name": "wb_get_supplies",
        "module": "warehouses",
        "description": "Список поставок",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "wb_get_supply_detail",
        "module": "warehouses",
        "description": "Детали конкретной поставки",
        "parameters": {
            "type": "object",
            "properties": {
                "supply_id": {"type": "string", "description": "ID поставки"},
            },
            "required": ["supply_id"],
        },
    },
    {
        "name": "wb_get_offices",
        "module": "warehouses",
        "description": "Список пунктов приёмки WB",
        "parameters": {"type": "object", "properties": {}},
    },
]

# Маппинг имя инструмента → функция
WAREHOUSE_HANDLERS = {
    "wb_get_warehouses": get_warehouses,
    "wb_get_warehouse_stocks": get_warehouse_stocks,
    "wb_get_supplies": get_supplies,
    "wb_get_supply_detail": get_supply_detail,
    "wb_get_offices": get_offices,
}
