import time

from app.clients.deribit_client import DeribitClient
from app.models.price import Price
from app.repositories.price_repository import PriceRepository
from app.schemas.price import Ticker


class PriceNotFoundError(Exception):
    def __init__(self, ticker: str) -> None:
        super().__init__(f"No prices stored for ticker {ticker!r}")
        self.ticker = ticker


class PriceService:
    def __init__(self, repository: PriceRepository, client: DeribitClient) -> None:
        self._repository = repository
        self._client = client

    async def collect(self, ticker: Ticker) -> Price:
        price = await self._client.get_index_price(ticker.value)
        return await self._repository.add(ticker.value, price, int(time.time()))

    async def collect_all(self) -> list[Price]:
        return [await self.collect(ticker) for ticker in Ticker]

    async def get_all(self, ticker: Ticker) -> list[Price]:
        prices = await self._repository.get_all(ticker.value)
        if not prices:
            raise PriceNotFoundError(ticker.value)
        return prices

    async def get_latest(self, ticker: Ticker) -> Price:
        price = await self._repository.get_latest(ticker.value)
        if price is None:
            raise PriceNotFoundError(ticker.value)
        return price

    async def get_by_date_range(
        self,
        ticker: Ticker,
        date_from: int | None = None,
        date_to: int | None = None,
    ) -> list[Price]:
        prices = await self._repository.get_by_date_range(
            ticker.value, date_from, date_to
        )
        if not prices:
            raise PriceNotFoundError(ticker.value)
        return prices
