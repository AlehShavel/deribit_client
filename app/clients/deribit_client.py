from decimal import Decimal, InvalidOperation
from types import TracebackType

import aiohttp


class DeribitClientError(Exception):
    pass


class DeribitClient:
    def __init__(
        self,
        base_url: str,
        timeout: int,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session = session
        self._owns_session = session is None

    async def __aenter__(self) -> "DeribitClient":
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        if self._session is not None and self._owns_session:
            await self._session.close()
            self._session = None

    async def get_index_price(self, index_name: str) -> Decimal:
        payload = await self._request(
            "public/get_index_price", {"index_name": index_name}
        )
        try:
            return Decimal(str(payload["result"]["index_price"]))
        except (KeyError, TypeError, InvalidOperation) as error:
            raise DeribitClientError(
                f"Unexpected response for index {index_name!r}: {payload!r}"
            ) from error

    async def _request(self, path: str, params: dict[str, str]) -> dict:
        if self._session is None:
            raise DeribitClientError("Client session is not initialized")

        url = f"{self._base_url}/{path}"
        try:
            async with self._session.get(
                url, params=params, timeout=self._timeout
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as error:
            raise DeribitClientError(f"Request to {url} failed: {error}") from error
        except TimeoutError as error:
            raise DeribitClientError(f"Request to {url} timed out") from error
