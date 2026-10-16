from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from app.clients.deribit_client import DeribitClient, DeribitClientError


def build_session(
    json_payload: dict | None = None, error: Exception | None = None
) -> MagicMock:
    response = MagicMock()
    response.json = AsyncMock(return_value=json_payload)
    response.raise_for_status = MagicMock()

    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.get = MagicMock(side_effect=error) if error else MagicMock(
        return_value=context
    )
    return session


async def test_get_index_price_returns_decimal() -> None:
    session = build_session({"result": {"index_price": 80806.57}})
    client = DeribitClient("https://example.com/api/v2", 10, session=session)

    price = await client.get_index_price("btc_usd")

    assert price == Decimal("80806.57")
    session.get.assert_called_once()
    assert session.get.call_args.kwargs["params"] == {"index_name": "btc_usd"}


async def test_get_index_price_raises_on_unexpected_payload() -> None:
    session = build_session({"error": {"message": "unknown index"}})
    client = DeribitClient("https://example.com/api/v2", 10, session=session)

    with pytest.raises(DeribitClientError):
        await client.get_index_price("sol_usd")


async def test_get_index_price_raises_on_network_error() -> None:
    session = build_session(error=aiohttp.ClientError("connection refused"))
    client = DeribitClient("https://example.com/api/v2", 10, session=session)

    with pytest.raises(DeribitClientError):
        await client.get_index_price("btc_usd")


async def test_request_without_session_raises() -> None:
    client = DeribitClient("https://example.com/api/v2", 10)

    with pytest.raises(DeribitClientError):
        await client.get_index_price("btc_usd")


async def test_provided_session_is_not_closed_by_client() -> None:
    session = build_session({"result": {"index_price": 1}})
    session.close = AsyncMock()
    client = DeribitClient("https://example.com/api/v2", 10, session=session)

    await client.close()

    session.close.assert_not_called()
