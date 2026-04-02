"""Модуль «Аналитика» — продажи, заказы, остатки, отчёты по номенклатурам."""

from __future__ import annotations

from typing import Any

from mcp_wb.src.wb_client import WBClient  # noqa: E402


async def get_sales(
    client: WBClient, date_from: str, date_to: str, flag: int = 0
) -> list[dict[str, Any]]:
    """Получить продажи за период.

    Args:
        date_from: Начало периода (RFC3339, например 2026-03-01).
        date_to: Конец периода.
        flag: 0 — с последнего запроса, 1 — за весь период.
    """
    return await client.get(
        "statistics",
        "/api/v1/supplier/sales",
        params={"dateFrom": date_from, "dateTo": date_to, "flag": flag},
    )


async def get_orders(
    client: WBClient, date_from: str, date_to: str, flag: int = 0
) -> list[dict[str, Any]]:
    """Получить заказы за период."""
    return await client.get(
        "statistics",
        "/api/v1/supplier/orders",
        params={"dateFrom": date_from, "dateTo": date_to, "flag": flag},
    )


async def get_stocks(client: WBClient) -> list[dict[str, Any]]:
    """Получить остатки на складах WB."""
    return await client.get(
        "statistics",
        "/api/v1/supplier/stocks",
        params={"dateFrom": "2019-01-01"},
    )


async def get_nm_report(
    client: WBClient,
    nm_ids: list[int],
    begin_date: str,
    end_date: str,
    page: int = 1,
) -> dict[str, Any]:
    """Получить детальный отчёт по номенклатурам (просмотры, корзина, заказы)."""
    return await client.post(
        "analytics",
        "/api/v1/analytics/nm-report/detail",
        json_body={
            "nmIDs": nm_ids,
            "period": {"begin": begin_date, "end": end_date},
            "page": page,
        },
    )


# Реестр инструментов модуля для MCP-сервера
ANALYTICS_TOOLS = [
    {
        "name": "wb_get_sales",
        "module": "analytics",
        "description": "Получить продажи за период (по товарам, по дням)",
        "parameters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Начало периода (YYYY-MM-DD)"},
                "date_to": {"type": "string", "description": "Конец периода (YYYY-MM-DD)"},
                "flag": {"type": "integer", "description": "0 — инкремент, 1 — за весь период", "default": 0},
            },
            "required": ["date_from", "date_to"],
        },
    },
    {
        "name": "wb_get_orders",
        "module": "analytics",
        "description": "Получить заказы за период",
        "parameters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Начало периода (YYYY-MM-DD)"},
                "date_to": {"type": "string", "description": "Конец периода (YYYY-MM-DD)"},
                "flag": {"type": "integer", "description": "0 — инкремент, 1 — за весь период", "default": 0},
            },
            "required": ["date_from", "date_to"],
        },
    },
    {
        "name": "wb_get_stocks",
        "module": "analytics",
        "description": "Получить остатки на складах WB",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "wb_get_nm_report",
        "module": "analytics",
        "description": "Детальный отчёт по номенклатурам (просмотры, корзина, заказы, выкупы)",
        "parameters": {
            "type": "object",
            "properties": {
                "nm_ids": {"type": "array", "items": {"type": "integer"}, "description": "Список nmID"},
                "begin_date": {"type": "string", "description": "Начало периода (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "Конец периода (YYYY-MM-DD)"},
                "page": {"type": "integer", "description": "Номер страницы", "default": 1},
            },
            "required": ["nm_ids", "begin_date", "end_date"],
        },
    },
]

# Маппинг имя инструмента → функция
ANALYTICS_HANDLERS = {
    "wb_get_sales": get_sales,
    "wb_get_orders": get_orders,
    "wb_get_stocks": get_stocks,
    "wb_get_nm_report": get_nm_report,
}
