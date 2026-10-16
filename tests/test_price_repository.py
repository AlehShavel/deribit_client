from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.price_repository import PriceRepository


@pytest.fixture
async def repository(session: AsyncSession) -> PriceRepository:
    repository = PriceRepository(session)
    await repository.add("btc_usd", Decimal("80000.5"), 1_700_000_000)
    await repository.add("btc_usd", Decimal("81000.5"), 1_700_000_060)
    await repository.add("eth_usd", Decimal("3000.5"), 1_700_000_120)
    return repository


async def test_add_stores_record(session: AsyncSession) -> None:
    repository = PriceRepository(session)

    record = await repository.add("btc_usd", Decimal("123.45"), 1_700_000_000)

    assert record.id is not None
    assert record.ticker == "btc_usd"
    assert record.price == Decimal("123.45")
    assert record.timestamp == 1_700_000_000


async def test_get_all_returns_only_requested_ticker(
    repository: PriceRepository,
) -> None:
    prices = await repository.get_all("btc_usd")

    assert [price.timestamp for price in prices] == [1_700_000_060, 1_700_000_000]


async def test_get_all_returns_empty_list_for_unknown_ticker(
    repository: PriceRepository,
) -> None:
    assert await repository.get_all("sol_usd") == []


async def test_get_latest_returns_newest_record(repository: PriceRepository) -> None:
    price = await repository.get_latest("btc_usd")

    assert price is not None
    assert price.timestamp == 1_700_000_060


async def test_get_latest_returns_none_for_unknown_ticker(
    repository: PriceRepository,
) -> None:
    assert await repository.get_latest("sol_usd") is None


async def test_get_by_date_range_filters_both_bounds(
    repository: PriceRepository,
) -> None:
    prices = await repository.get_by_date_range(
        "btc_usd", date_from=1_700_000_030, date_to=1_700_000_070
    )

    assert [price.timestamp for price in prices] == [1_700_000_060]


async def test_get_by_date_range_without_bounds_returns_all(
    repository: PriceRepository,
) -> None:
    prices = await repository.get_by_date_range("btc_usd")

    assert len(prices) == 2
