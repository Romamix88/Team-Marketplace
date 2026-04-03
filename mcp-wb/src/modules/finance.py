"""Модуль «Финансы» — финансовые отчёты, комиссии, штрафы, хранение."""

from __future__ import annotations

from typing import Any

from mcp_wb.src.wb_client import WBClient  # noqa: E402


async def get_financial_report(
    client: WBClient, date_from: str, date_to: str
) -> list[dict[str, Any]]:
    """Получить детализированный финансовый отчёт за период.

    Включает: комиссии WB, логистику, штрафы, компенсации, хранение.
    """
    return await client.get(
        "statistics",
        "/api/v5/supplier/reportDetailByPeriod",
        params={"dateFrom": date_from, "dateTo": date_to},
    )


async def get_incomes(
    client: WBClient, date_from: str
) -> list[dict[str, Any]]:
    """Получить поступления (приёмки на склад WB)."""
    return await client.get(
        "statistics",
        "/api/v1/supplier/incomes",
        params={"dateFrom": date_from},
    )


async def get_paid_storage(
    client: WBClient, date_from: str, date_to: str
) -> list[dict[str, Any]]:
    """Получить отчёт о платном хранении по товарам."""
    return await client.post(
        "analytics",
        "/api/v1/analytics/paid-storage",
        json_body={"dateFrom": date_from, "dateTo": date_to},
    )


# Реестр инструментов модуля
FINANCE_TOOLS = [
    {
        "name": "wb_get_financial_report",
        "module": "finance",
        "description": "Детализированный финансовый отчёт (комиссии, логистика, штрафы, компенсации)",
        "parameters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Начало периода (YYYY-MM-DD)"},
                "date_to": {"type": "string", "description": "Конец периода (YYYY-MM-DD)"},
            },
            "required": ["date_from", "date_to"],
        },
    },
    {
        "name": "wb_get_incomes",
        "module": "finance",
        "description": "Поступления (приёмки на склад WB)",
        "parameters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Начало периода (YYYY-MM-DD)"},
            },
            "required": ["date_from"],
        },
    },
    {
        "name": "wb_get_paid_storage",
        "module": "finance",
        "description": "Отчёт о платном хранении по товарам",
        "parameters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Начало периода (YYYY-MM-DD)"},
                "date_to": {"type": "string", "description": "Конец периода (YYYY-MM-DD)"},
            },
            "required": ["date_from", "date_to"],
        },
    },
]

FINANCE_HANDLERS = {
    "wb_get_financial_report": get_financial_report,
    "wb_get_incomes": get_incomes,
    "wb_get_paid_storage": get_paid_storage,
}
