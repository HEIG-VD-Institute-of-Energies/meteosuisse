from __future__ import annotations

from typing import Any

import httpx
import orjson
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import APIConfig
from .exceptions import MeteoSwissAPIError


class HttpClient:
    def __init__(self, config: APIConfig):
        self._config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            headers=config.headers(),
            timeout=config.httpx_timeout(),
            limits=config.httpx_limits(),
            http2=False,
            follow_redirects=True,
            trust_env=False,
        )

    def close(self) -> None:
        self._client.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            r = self._client.get(path, params=params)
            r.raise_for_status()
            return orjson.loads(r.content)
        except httpx.HTTPStatusError as e:
            raise MeteoSwissAPIError(f"HTTP {e.response.status_code} for {path}") from e
        except httpx.HTTPError as e:
            raise MeteoSwissAPIError(str(e)) from e
