"""Модуль «Реклама» — кампании, ставки, бюджеты, статистика."""

from __future__ import annotations

from typing import Any

from mcp_wb.src.wb_client import WBClient  # noqa: E402


# === Чтение ===

async def get_campaigns_count(client: WBClient) -> dict[str, Any]:
    """Получить количество кампаний по статусам."""
    return await client.get("advertising", "/adv/v1/promotion/count")


async def get_campaigns(
    client: WBClient, status: int | None = None
) -> list[dict[str, Any]]:
    """Получить список рекламных кампаний."""
    params: dict[str, Any] = {}
    if status is not None:
        params["status"] = status
    return await client.get("advertising", "/adv/v1/promotion/adverts", params=params or None)


async def get_campaign_stats(
    client: WBClient, campaign_ids: list[int]
) -> list[dict[str, Any]]:
    """Получить полную статистику кампаний (показы, клики, CTR, CPC, расход)."""
    return await client.post(
        "advertising", "/adv/v2/fullstats", json_body=campaign_ids
    )


async def get_keyword_stats(
    client: WBClient, campaign_id: int
) -> dict[str, Any]:
    """Получить статистику по ключевым словам кампании."""
    return await client.get(
        "advertising", "/adv/v1/stat/words", params={"id": campaign_id}
    )


# === Запись (требует одобрения) ===

async def start_campaign(
    client: WBClient, campaign_id: int
) -> dict[str, Any]:
    """Запустить рекламную кампанию."""
    return await client.post(
        "advertising", "/adv/v1/start", json_body={"id": campaign_id}
    )


async def pause_campaign(
    client: WBClient, campaign_id: int
) -> dict[str, Any]:
    """Поставить кампанию на паузу."""
    return await client.post(
        "advertising", "/adv/v1/pause", json_body={"id": campaign_id}
    )


async def set_campaign_budget(
    client: WBClient, campaign_id: int, amount: int
) -> dict[str, Any]:
    """Пополнить бюджет кампании."""
    return await client.post(
        "advertising",
        "/adv/v1/budget/deposit",
        json_body={"id": campaign_id, "sum": amount},
    )


async def set_campaign_cpm(
    client: WBClient, campaign_id: int, cpm: int, param: int = 0
) -> dict[str, Any]:
    """Изменить ставку CPM кампании."""
    return await client.post(
        "advertising",
        "/adv/v1/cpm",
        json_body={"advertId": campaign_id, "cpm": cpm, "param": param},
    )


# === Реестр инструментов ===

ADVERTISING_TOOLS = [
    {
        "name": "wb_adv_get_campaigns_count",
        "module": "advertising",
        "description": "Количество рекламных кампаний по статусам",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "wb_adv_get_campaigns",
        "module": "advertising",
        "description": "Список рекламных кампаний (можно фильтровать по статусу)",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "integer", "description": "Статус: 4=готова, 7=завершена, 9=активна, 11=на паузе"},
            },
        },
    },
    {
        "name": "wb_adv_get_campaign_stats",
        "module": "advertising",
        "description": "Полная статистика кампаний (показы, клики, CTR, CPC, расход, ДРР)",
        "parameters": {
            "type": "object",
            "properties": {
                "campaign_ids": {"type": "array", "items": {"type": "integer"}, "description": "Список ID кампаний"},
            },
            "required": ["campaign_ids"],
        },
    },
    {
        "name": "wb_adv_get_keyword_stats",
        "module": "advertising",
        "description": "Статистика по ключевым словам конкретной кампании",
        "parameters": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer", "description": "ID кампании"},
            },
            "required": ["campaign_id"],
        },
    },
    {
        "name": "wb_adv_start_campaign",
        "module": "advertising",
        "description": "Запустить рекламную кампанию. ТРЕБУЕТ ОДОБРЕНИЯ.",
        "parameters": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer", "description": "ID кампании"},
            },
            "required": ["campaign_id"],
        },
    },
    {
        "name": "wb_adv_pause_campaign",
        "module": "advertising",
        "description": "Поставить рекламную кампанию на паузу. ТРЕБУЕТ ОДОБРЕНИЯ.",
        "parameters": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer", "description": "ID кампании"},
            },
            "required": ["campaign_id"],
        },
    },
    {
        "name": "wb_adv_set_budget",
        "module": "advertising",
        "description": "Пополнить бюджет рекламной кампании. ТРЕБУЕТ ОДОБРЕНИЯ.",
        "parameters": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer", "description": "ID кампании"},
                "amount": {"type": "integer", "description": "Сумма пополнения (руб)"},
            },
            "required": ["campaign_id", "amount"],
        },
    },
    {
        "name": "wb_adv_set_cpm",
        "module": "advertising",
        "description": "Изменить ставку CPM кампании",
        "parameters": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "integer", "description": "ID кампании"},
                "cpm": {"type": "integer", "description": "Новая ставка CPM (руб)"},
            },
            "required": ["campaign_id", "cpm"],
        },
    },
]

ADVERTISING_HANDLERS = {
    "wb_adv_get_campaigns_count": get_campaigns_count,
    "wb_adv_get_campaigns": get_campaigns,
    "wb_adv_get_campaign_stats": get_campaign_stats,
    "wb_adv_get_keyword_stats": get_keyword_stats,
    "wb_adv_start_campaign": start_campaign,
    "wb_adv_pause_campaign": pause_campaign,
    "wb_adv_set_budget": set_campaign_budget,
    "wb_adv_set_cpm": set_campaign_cpm,
}
