# CONTEXT.md — Текущее состояние проекта

> Последнее обновление: 03 апреля 2026
> Текущая фаза: **Фаза 0 завершена ✅ — готовы к Фазе 1**

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

### Инфраструктура — Фаза 0 ✅ (развёрнуто на VPS)
- [x] VPS: 147.45.154.46, Timeweb Cloud, Docker + Docker Compose
- [x] Redis 7 — шина сообщений (контейнер, healthy)
- [x] MCP-сервер WB — модули analytics + warehouses (FastAPI, порт 8001)
- [x] Telegram-бот — aiogram 3.x, команды /status, /tasks, inline-одобрения
- [x] Дашборд — FastAPI + Jinja2 + HTMX (порт 8080, http://147.45.154.46:8080)
- [x] docker-compose.yml — 4 сервиса: redis, mcp-wb, telegram-bot, dashboard
- [x] .env — заполнен на VPS (6 WB-токенов, RouterAI, Telegram, Redis)

### Код Фазы 0 ✅
- [x] `shared/models.py` — Task, TaskStatus, AgentStatus, ApprovalRequest, ApprovalResult, ToolCallRequest/Response
- [x] `shared/message_bus.py` — Redis: очереди задач (BLPOP), pub/sub, shared state, approval
- [x] `shared/task_manager.py` — create_and_assign, update_status, get_recent
- [x] `shared/approval.py` — request_approval (publish + poll), submit_approval_result
- [x] `shared/logging_config.py` — structlog JSON
- [x] `mcp-wb/src/wb_client.py` — httpx async, Bearer auth, retry (429→backoff), rate limit (semaphore)
- [x] `mcp-wb/src/modules/analytics.py` — get_sales, get_orders, get_stocks, get_nm_report
- [x] `mcp-wb/src/modules/warehouses.py` — get_warehouses, get_warehouse_stocks, get_supplies, get_supply_detail, get_offices
- [x] `mcp-wb/src/auth/access.py` — AGENT_ACCESS, AGENT_TOKEN_ENV, get_agent_token, filter_tools
- [x] `mcp-wb/src/server.py` — FastAPI: /tools/call, /tools/list, /health; пул клиентов по агентам (lazy init)
- [x] `agents/base/tools.py` — McpClient (HTTP к MCP), RouterAIClient (OpenAI-compatible)
- [x] `agents/base/agent.py` — BaseAgent: main loop, heartbeat, execute_task, LLM-цикл с tool calling
- [x] `telegram-bot/src/bot.py` — /start, /status, /tasks, /help; approval listener (pub/sub); whitelist chat_id
- [x] `dashboard/src/app.py` — FastAPI + Jinja2 + HTMX; авто-обновление каждые 5 сек

### 1С (отложено на Фазу 3+)
- [ ] WireGuard туннель (VPS → офис) — НЕ НАСТРОЕН
- [ ] Сервисные пользователи (ReadOnly, Operator) — НЕ СОЗДАНЫ
- [ ] MCP-сервер 1С — НЕ РАЗРАБОТАН

## Что делаем дальше

### Фаза 1 — Аналитик + Логист (следующий шаг)

**Что нужно разработать:**
1. Модули MCP-WB: `prices` и `finance` (чтение)
2. Агент `agent-wb-analyst`: config.yml, system.md (системный промпт), Dockerfile, agent.py
3. Агент `agent-wb-logistics`: config.yml, system.md, Dockerfile, agent.py
4. Добавить контейнеры агентов в docker-compose.yml
5. Ежедневные отчёты в Telegram
6. Тестирование на реальных данных WB

**Результат Фазы 1:**
- Ежедневные отчёты по продажам, маржинальности, остаткам
- Рекомендации по ценам (с одобрением через Telegram)
- План поставок (с одобрением через Telegram)

## Открытые вопросы

1. **RouterAI бюджет**: оценить стоимость при планируемой нагрузке после пилота Фазы 1
2. **Масштабирование VPS**: когда переходить с 8 ГБ на 16 ГБ RAM (ориентир — Фаза 2)
3. **Ozon и ЯМ**: когда начинать адаптацию (после стабильной работы WB-команды)
4. **1С интеграция**: на какой фазе подключать (ориентир — Фаза 3)
5. **Безопасность VPS**: настроить firewall (UFW), закрыть лишние порты, SSH-ключи вместо паролей

## Решения, принятые ранее

| Дата | Решение | Обоснование |
|---|---|---|
| 01.04.2026 | Всё на VPS, без отдельного сервера в офисе | Упрощение инфраструктуры, единая точка управления |
| 01.04.2026 | RouterAI как LLM-провайдер | Единый API ко всем моделям, оплата в рублях |
| 01.04.2026 | Модель подбирается под агента | Claude для сложного анализа, DeepSeek для рутины |
| 02.04.2026 | Фокус на маркетплейсы (WB первый) | Прямое влияние на продажи, быстрый ROI |
| 02.04.2026 | Telegram + Дашборд для связи | Telegram — одобрения, дашборд — аналитика |
| 02.04.2026 | Только WB API на старте (без 1С) | Быстрый старт, минимум зависимостей |
| 02.04.2026 | Redis как шина сообщений | pub/sub + очереди задач |
| 02.04.2026 | Human-in-the-loop через Telegram | Критичные операции: цены, реклама, поставки, контент |
| 03.04.2026 | 6 раздельных WB-токенов | Принцип минимальных привилегий, изоляция агентов |
| 03.04.2026 | VPS: Timeweb Cloud 147.45.154.46 | Российский провайдер, оплата в рублях |
| 03.04.2026 | MCP-сервер — HTTP REST (FastAPI) | Простота, Docker-совместимость, пул клиентов по агентам |

## Метрики проекта

| Метрика | Значение |
|---|---|
| Всего агентов WB (план) | 6 |
| Агентов в проде | 0 (BaseAgent готов, агенты запускаются в Фазе 1) |
| MCP-серверов в проде | 1 (MCP-WB) |
| Модулей MCP-WB в проде | 2 (analytics, warehouses) |
| Модулей MCP-WB (план) | 6 |
| Инструментов MCP в проде | 9 |
| Инструментов MCP (план) | ~40 |
| Контейнеров на VPS | 4 (redis, mcp-wb, telegram-bot, dashboard) |
| Текущая фаза | Фаза 0 ✅ завершена |
| Следующая фаза | Фаза 1 — Аналитик + Логист |
