from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.models.price import Price
from app.schemas.price import Ticker
from app.services.price_service import PriceNotFoundError, PriceService


def build_service(repository: AsyncMock, client: AsyncMock) -> PriceService:
    return PriceService(repository, client)


async def test_collect_stores_price_from_client() -> None:
    client = AsyncMock()
    client.get_index_price.return_value = Decimal("80806.57")
    repository = AsyncMock()
    service = build_service(repository, client)

    await service.collect(Ticker.BTC_USD)

    client.get_index_price.assert_awaited_once_with("btc_usd")
    ticker, price, timestamp = repository.add.await_args.args
    assert ticker == "btc_usd"
    assert price == Decimal("80806.57")
    assert isinstance(timestamp, int)


async def test_collect_all_covers_every_ticker() -> None:
    client = AsyncMock()
    client.get_index_price.return_value = Decimal("1")
    repository = AsyncMock()
    service = build_service(repository, client)

    await service.collect_all()

    requested = [call.args[0] for call in client.get_index_price.await_args_list]
    assert requested == [ticker.value for ticker in Ticker]


async def test_get_all_returns_repository_records() -> None:
    records = [Price(ticker="btc_usd", price=Decimal("1"), timestamp=1)]
    repository = AsyncMock()
    repository.get_all.return_value = records
    service = build_service(repository, AsyncMock())

    assert await service.get_all(Ticker.BTC_USD) == records


async def test_get_all_raises_when_empty() -> None:
    repository = AsyncMock()
    repository.get_all.return_value = []
    service = build_service(repository, AsyncMock())

    with pytest.raises(PriceNotFoundError):
        await service.get_all(Ticker.BTC_USD)


async def test_get_latest_raises_when_missing() -> None:
    repository = AsyncMock()
    repository.get_latest.return_value = None
    service = build_service(repository, AsyncMock())

    with pytest.raises(PriceNotFoundError):
        await service.get_latest(Ticker.ETH_USD)


async def test_get_by_date_range_passes_bounds_to_repository() -> None:
    repository = AsyncMock()
    repository.get_by_date_range.return_value = [
        Price(ticker="btc_usd", price=Decimal("1"), timestamp=5)
    ]
    service = build_service(repository, AsyncMock())

    await service.get_by_date_range(Ticker.BTC_USD, 1, 10)

    repository.get_by_date_range.assert_awaited_once_with("btc_usd", 1, 10)


async def test_get_by_date_range_raises_when_empty() -> None:
    repository = AsyncMock()
    repository.get_by_date_range.return_value = []
    service = build_service(repository, AsyncMock())

    with pytest.raises(PriceNotFoundError):
        await service.get_by_date_range(Ticker.BTC_USD, 1, 10)
