"""HTTP-клиент к Wildberries API с retry и rate limiting."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import httpx
import structlog
import yaml

logger = structlog.get_logger()

# Загрузка конфигурации
_CONFIG_PATH = Path(__file__).parent.parent / "config.yml"


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


class WBApiError(Exception):
    """Ошибка WB API."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"WB API {status_code}: {detail}")


class WBClient:
    """Async HTTP-клиент к Wildberries API."""

    def __init__(
        self,
        api_token: str,
        config: dict | None = None,
    ) -> None:
        self._token = api_token
        self._config = config or _load_config()
        wb = self._config["wb_api"]
        self._base_urls: dict[str, str] = wb["base_urls"]
        self._max_retries: int = wb["rate_limit"]["max_retries"]
        self._backoff_base: float = wb["rate_limit"]["backoff_base"]
        self._timeout: int = wb.get("timeout", 30)
        self._semaphore = asyncio.Semaphore(wb["rate_limit"]["default_rps"])
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout),
            headers={
                "Authorization": self._token,
                "Content-Type": "application/json",
            },
        )

    def _url(self, section: str, path: str) -> str:
        """Сформировать полный URL."""
        base = self._base_urls.get(section)
        if base is None:
            raise ValueError(f"Неизвестная секция WB API: {section}")
        return f"{base}{path}"

    async def get(
        self, section: str, path: str, params: dict[str, Any] | None = None
    ) -> Any:
        """GET-запрос к WB API с retry."""
        url = self._url(section, path)
        return await self._request("GET", url, params=params)

    async def post(
        self, section: str, path: str, json_body: dict[str, Any] | None = None
    ) -> Any:
        """POST-запрос к WB API с retry."""
        url = self._url(section, path)
        return await self._request("POST", url, json=json_body)

    async def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Выполнить HTTP-запрос с retry и backoff."""
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            async with self._semaphore:
                try:
                    resp = await self._client.request(method, url, **kwargs)

                    if resp.status_code == 429:
                        wait = self._backoff_base * (2**attempt)
                        logger.warning(
                            "wb_rate_limited",
                            url=url,
                            attempt=attempt,
                            wait=wait,
                        )
                        await asyncio.sleep(wait)
                        continue

                    if resp.status_code >= 500:
                        wait = self._backoff_base * (2**attempt)
                        logger.warning(
                            "wb_server_error",
                            url=url,
                            status=resp.status_code,
                            attempt=attempt,
                        )
                        await asyncio.sleep(wait)
                        continue

                    if resp.status_code >= 400:
                        raise WBApiError(resp.status_code, resp.text)

                    logger.debug("wb_request_ok", url=url, status=resp.status_code)
                    return resp.json() if resp.text else {}

                except httpx.TimeoutException as exc:
                    last_error = exc
                    logger.warning("wb_timeout", url=url, attempt=attempt)
                    await asyncio.sleep(self._backoff_base * (2**attempt))

        raise last_error or WBApiError(0, "Все попытки исчерпаны")

    async def close(self) -> None:
        """Закрыть HTTP-клиент."""
        await self._client.aclose()
