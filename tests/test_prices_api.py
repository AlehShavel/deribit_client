from collections.abc import Iterator
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_price_service
from app.core.config import Settings
from app.main import create_app
from app.models.price import Price
from app.services.price_service import PriceNotFoundError

SETTINGS = Settings(
    database_url="postgresql+asyncpg://user:pass@localhost:5432/test",
    redis_url="redis://localhost:6379/0",
)


@pytest.fixture
def service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(service: AsyncMock) -> Iterator[TestClient]:
    app = create_app(SETTINGS)
    app.dependency_overrides[get_price_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client


def build_price(timestamp: int = 1_700_000_000) -> Price:
    return Price(ticker="btc_usd", price=Decimal("80806.57"), timestamp=timestamp)


def test_get_prices_returns_records(client: TestClient, service: AsyncMock) -> None:
    service.get_all.return_value = [build_price()]

    response = client.get("/prices", params={"ticker": "btc_usd"})

    assert response.status_code == 200
    assert response.json() == [
        {"ticker": "btc_usd", "price": "80806.57", "timestamp": 1_700_000_000}
    ]


def test_get_latest_price_returns_single_record(
    client: TestClient, service: AsyncMock
) -> None:
    service.get_latest.return_value = build_price()

    response = client.get("/prices/latest", params={"ticker": "btc_usd"})

    assert response.status_code == 200
    assert response.json()["ticker"] == "btc_usd"


def test_get_prices_by_date_passes_bounds(
    client: TestClient, service: AsyncMock
) -> None:
    service.get_by_date_range.return_value = [build_price()]

    response = client.get(
        "/prices/filter",
        params={"ticker": "btc_usd", "date_from": 1, "date_to": 2_000_000_000},
    )

    assert response.status_code == 200
    assert service.get_by_date_range.await_args.args[1:] == (1, 2_000_000_000)


def test_missing_ticker_is_rejected(client: TestClient) -> None:
    assert client.get("/prices").status_code == 422


def test_unknown_ticker_is_rejected(client: TestClient) -> None:
    assert client.get("/prices", params={"ticker": "sol_usd"}).status_code == 422


def test_negative_date_bound_is_rejected(client: TestClient) -> None:
    response = client.get(
        "/prices/filter", params={"ticker": "btc_usd", "date_from": -1}
    )

    assert response.status_code == 422


def test_missing_data_returns_not_found(
    client: TestClient, service: AsyncMock
) -> None:
    service.get_latest.side_effect = PriceNotFoundError("btc_usd")

    response = client.get("/prices/latest", params={"ticker": "btc_usd"})

    assert response.status_code == 404
    assert "btc_usd" in response.json()["detail"]
