"""Модуль «Цены» — текущие цены, загрузка новых цен, скидки."""

from __future__ import annotations

from typing import Any

from mcp_wb.src.wb_client import WBClient  # noqa: E402


async def get_prices(
    client: WBClient, limit: int = 1000, offset: int = 0
) -> dict[str, Any]:
    """Получить текущие цены на товары."""
    return await client.get(
        "marketplace",
        "/api/v2/list/goods/filter",
        params={"limit": limit, "offset": offset},
    )


async def get_price_by_nm(
    client: WBClient, nm_id: int
) -> dict[str, Any]:
    """Получить цену по nmID."""
    return await client.get(
        "marketplace",
        "/api/v2/list/goods/size/nm",
        params={"nmID": nm_id},
    )


async def get_goods_list(
    client: WBClient, limit: int = 1000, offset: int = 0,
    filter_nm_id: int | None = None,
) -> dict[str, Any]:
    """Получить список товаров с ценами и скидками."""
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if filter_nm_id is not None:
        params["filterNmID"] = filter_nm_id
    return await client.get(
        "marketplace",
        "/api/v2/list/goods/filter",
        params=params,
    )


# Реестр инструментов модуля
PRICES_TOOLS = [
    {
        "name": "wb_get_prices",
        "module": "prices",
        "description": "Получить текущие цены на товары (список с пагинацией)",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Кол-во записей (макс 1000)", "default": 1000},
                "offset": {"type": "integer", "description": "Смещение", "default": 0},
            },
        },
    },
    {
        "name": "wb_get_price_by_nm",
        "module": "prices",
        "description": "Получить цену конкретного товара по nmID",
        "parameters": {
            "type": "object",
            "properties": {
                "nm_id": {"type": "integer", "description": "nmID товара"},
            },
            "required": ["nm_id"],
        },
    },
    {
        "name": "wb_get_goods_list",
        "module": "prices",
        "description": "Список товаров с ценами и скидками",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 1000},
                "offset": {"type": "integer", "default": 0},
                "filter_nm_id": {"type": "integer", "description": "Фильтр по nmID (опционально)"},
            },
        },
    },
]

PRICES_HANDLERS = {
    "wb_get_prices": get_prices,
    "wb_get_price_by_nm": get_price_by_nm,
    "wb_get_goods_list": get_goods_list,
}
