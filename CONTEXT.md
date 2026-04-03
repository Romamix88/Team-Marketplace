# CONTEXT.md — Текущее состояние проекта

> Последнее обновление: 03 апреля 2026
> Текущая фаза: **Фаза 1 завершена ✅ — готовы к Фазе 2**

## Что уже сделано

### Проектирование ✅
- [x] Определена цель: автономная команда AI-агентов для управления кабинетом WB
- [x] Определены 6 агентов WB и их зоны ответственности
- [x] Определена модульная структура MCP-сервера WB (6 модулей)
- [x] Составлена дорожная карта из 4 фаз (~10 недель)
- [x] Выбран подход к коммуникации агентов: Redis (pub/sub + очереди задач)
- [x] Выбран канал связи с владельцем: Telegram-бот + веб-дашборд
- [x] Выбран LLM-провайдер: RouterAI (routerai.ru)
- [x] Определены модели под каждого агента
- [x] Обновлена вся документация (CLAUDE.md, AGENTS.md, CONTEXT.md, PROJECT_SPEC.md)

### Доступы ✅
- [x] WB API-токены — 6 раздельных токенов (по агенту, принцип минимальных привилегий)
- [x] RouterAI API key — получен
- [x] Telegram Bot Token — получен
- [x] Telegram Admin Chat ID — получен
- [x] VPS арендован — 147.45.154.46 (Timeweb Cloud)
- [x] GitHub репозиторий — публичный (git pull работает без авторизации)

### Инфраструктура — Фаза 0 ✅ (развёрнуто на VPS)
- [x] VPS: 147.45.154.46, Timeweb Cloud, Docker + Docker Compose
- [x] Redis 7 — шина сообщений (контейнер, healthy)
- [x] MCP-сервер WB — 4 модуля, 15 инструментов (FastAPI, порт 8001)
- [x] Telegram-бот — aiogram 3.x, команды /status, /tasks, inline-одобрения
- [x] Дашборд — FastAPI + Jinja2 + HTMX (порт 8080, http://147.45.154.46:8080)
- [x] docker-compose.yml — 6 сервисов на VPS
- [x] .env — заполнен на VPS (6 WB-токенов, RouterAI, Telegram, Redis)

### Код Фазы 0 ✅
- [x] `shared/` — models, message_bus, task_manager, approval, logging_config
- [x] `mcp-wb/` — server.py, wb_client.py, auth/access.py
- [x] `mcp-wb/src/modules/analytics.py` — get_sales, get_orders, get_stocks, get_nm_report
- [x] `mcp-wb/src/modules/warehouses.py` — get_warehouses, get_warehouse_stocks, get_supplies, get_supply_detail, get_offices
- [x] `agents/base/` — BaseAgent (LLM-цикл + MCP + Redis), McpClient, RouterAIClient
- [x] `telegram-bot/` — bot.py (aiogram 3.x)
- [x] `dashboard/` — app.py (FastAPI + Jinja2 + HTMX)

### Фаза 1 ✅ (развёрнуто на VPS)
- [x] `mcp-wb/src/modules/prices.py` — get_prices, get_price_by_nm, get_goods_list (3 инструмента)
- [x] `mcp-wb/src/modules/finance.py` — get_financial_report, get_incomes, get_paid_storage (3 инструмента)
- [x] `agents/wb-analyst/` — config.yml (DeepSeek V3), system.md (unit-экономика, ABC-анализ, рекомендации по ценам), agent.py, Dockerfile
- [x] `agents/wb-logistics/` — config.yml (Claude Sonnet 4.6), system.md (остатки, скорость продаж, план поставок, out-of-stock), agent.py, Dockerfile
- [x] docker-compose.yml — добавлены agent-wb-analyst и agent-wb-logistics
- [x] Всё развёрнуто на VPS: 6 контейнеров работают

### 1С (отложено на Фазу 3+)
- [ ] WireGuard туннель (VPS → офис) — НЕ НАСТРОЕН
- [ ] Сервисные пользователи (ReadOnly, Operator) — НЕ СОЗДАНЫ
- [ ] MCP-сервер 1С — НЕ РАЗРАБОТАН

## Что делаем дальше

### Фаза 2 — Контент-менеджер + Маркетолог (следующий шаг)

**Что нужно разработать:**
1. Модули MCP-WB: `content` и `advertising` (чтение + запись)
2. Агент `agent-wb-content`: config.yml, system.md, Dockerfile, agent.py
3. Агент `agent-wb-marketing`: config.yml, system.md, Dockerfile, agent.py
4. Добавить контейнеры агентов в docker-compose.yml
5. Human-in-the-loop: одобрение изменений контента и рекламных кампаний
6. A/B тестирование контента карточек

**Результат Фазы 2:**
- Автоматическая оптимизация карточек товаров (SEO, описания, A/B тесты CTR)
- Управление рекламными кампаниями (создание, пауза, оптимизация ДРР)
- Одобрение всех изменений через Telegram

## Открытые вопросы

1. **RouterAI бюджет**: оценить стоимость при планируемой нагрузке после пилота
2. **Масштабирование VPS**: когда переходить с 8 ГБ на 16 ГБ RAM (ориентир — Фаза 2-3)
3. **Ozon и ЯМ**: когда начинать адаптацию (после стабильной работы WB-команды)
4. **1С интеграция**: на какой фазе подключать (ориентир — Фаза 3)
5. **Безопасность VPS**: настроить firewall (UFW), закрыть лишние порты, SSH-ключи

## Решения, принятые ранее

| Дата | Решение | Обоснование |
|---|---|---|
| 01.04.2026 | Всё на VPS, без отдельного сервера в офисе | Упрощение инфраструктуры |
| 01.04.2026 | RouterAI как LLM-провайдер | Единый API, оплата в рублях |
| 01.04.2026 | Модель подбирается под агента | Claude для сложного, DeepSeek для рутины |
| 02.04.2026 | Фокус на маркетплейсы (WB первый) | Прямое влияние на продажи |
| 02.04.2026 | Telegram + Дашборд для связи | Telegram — одобрения, дашборд — аналитика |
| 02.04.2026 | Только WB API на старте (без 1С) | Быстрый старт, минимум зависимостей |
| 02.04.2026 | Redis как шина сообщений | pub/sub + очереди задач |
| 02.04.2026 | Human-in-the-loop через Telegram | Критичные: цены, реклама, поставки, контент |
| 03.04.2026 | 6 раздельных WB-токенов | Принцип минимальных привилегий |
| 03.04.2026 | VPS: Timeweb Cloud 147.45.154.46 | Российский провайдер, оплата в рублях |
| 03.04.2026 | MCP-сервер — HTTP REST (FastAPI) | Простота, пул клиентов по агентам |
| 03.04.2026 | GitHub репозиторий публичный | Упрощение деплоя (git pull без авторизации) |

## Процесс деплоя обновлений на VPS

```bash
cd /opt/Team-Marketplace
git pull origin claude/ai-marketplace-agents-plan-28PEX
docker compose up -d --build
```

## Метрики проекта

| Метрика | Значение |
|---|---|
| Всего агентов WB (план) | 6 |
| Агентов в проде | 2 (analyst, logistics) |
| MCP-серверов в проде | 1 (MCP-WB) |
| Модулей MCP-WB в проде | 4 (analytics, warehouses, prices, finance) |
| Модулей MCP-WB (план) | 6 |
| Инструментов MCP в проде | 15 |
| Инструментов MCP (план) | ~25 |
| Контейнеров на VPS | 6 (redis, mcp-wb, analyst, logistics, telegram-bot, dashboard) |
| Текущая фаза | Фаза 1 ✅ завершена |
| Следующая фаза | Фаза 2 — Контент-менеджер + Маркетолог |
