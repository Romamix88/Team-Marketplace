"""Модуль «Контент» — карточки товаров, описания, характеристики, медиа."""

from __future__ import annotations

from typing import Any

from mcp_wb.src.wb_client import WBClient  # noqa: E402


# === Чтение ===

async def get_cards_list(
    client: WBClient,
    limit: int = 100,
    cursor: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Получить список карточек товаров."""
    body: dict[str, Any] = {
        "settings": {"cursor": cursor or {"limit": limit}, "filter": {"withPhoto": -1}},
    }
    return await client.post("content", "/content/v2/get/cards/list", json_body=body)


async def get_card_detail(
    client: WBClient, nm_id: int
) -> dict[str, Any]:
    """Получить детальную информацию по карточке."""
    body = {
        "settings": {"cursor": {"limit": 1}, "filter": {"withPhoto": -1}},
        "vendorCodes": [],
        "allowedCategoriesOnly": False,
    }
    result = await client.post("content", "/content/v2/get/cards/list", json_body=body)
    # Фильтруем по nmID из результатов
    cards = result.get("cards", [])
    for card in cards:
        if card.get("nmID") == nm_id:
            return card
    return {"error": f"Карточка nmID={nm_id} не найдена"}


async def get_categories(client: WBClient) -> list[dict[str, Any]]:
    """Получить справочник категорий WB."""
    return await client.get("content", "/content/v2/object/all", params={"locale": "ru"})


async def get_category_charcs(
    client: WBClient, subject_id: int
) -> list[dict[str, Any]]:
    """Получить характеристики категории (обязательные и рекомендуемые поля)."""
    return await client.get(
        "content", f"/content/v2/object/charcs/{subject_id}", params={"locale": "ru"}
    )


# === Запись (требует одобрения) ===

async def update_card(
    client: WBClient, cards: list[dict[str, Any]]
) -> dict[str, Any]:
    """Обновить карточку товара (описание, характеристики)."""
    return await client.post("content", "/content/v2/cards/update", json_body=cards)


# === Реестр инструментов ===

CONTENT_TOOLS = [
    {
        "name": "wb_get_cards_list",
        "module": "content",
        "description": "Список карточек товаров (с пагинацией)",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Кол-во карточек (макс 100)", "default": 100},
            },
        },
    },
    {
        "name": "wb_get_card_detail",
        "module": "content",
        "description": "Детальная информация по карточке товара (описание, характеристики, фото)",
        "parameters": {
            "type": "object",
            "properties": {
                "nm_id": {"type": "integer", "description": "nmID товара"},
            },
            "required": ["nm_id"],
        },
    },
    {
        "name": "wb_get_categories",
        "module": "content",
        "description": "Справочник категорий WB",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "wb_get_category_charcs",
        "module": "content",
        "description": "Характеристики категории (обязательные и рекомендуемые поля)",
        "parameters": {
            "type": "object",
            "properties": {
                "subject_id": {"type": "integer", "description": "ID категории (subjectId)"},
            },
            "required": ["subject_id"],
        },
    },
    {
        "name": "wb_update_card",
        "module": "content",
        "description": "Обновить карточку товара (описание, характеристики). ТРЕБУЕТ ОДОБРЕНИЯ.",
        "parameters": {
            "type": "object",
            "properties": {
                "cards": {
                    "type": "array",
                    "description": "Массив карточек для обновления (формат WB API)",
                    "items": {"type": "object"},
                },
            },
            "required": ["cards"],
        },
    },
]

CONTENT_HANDLERS = {
    "wb_get_cards_list": get_cards_list,
    "wb_get_card_detail": get_card_detail,
    "wb_get_categories": get_categories,
    "wb_get_category_charcs": get_category_charcs,
    "wb_update_card": update_card,
}
