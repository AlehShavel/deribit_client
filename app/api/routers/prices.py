from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import PriceServiceDep
from app.schemas.price import PriceRead, Ticker

router = APIRouter(prefix="/prices", tags=["prices"])

TickerQuery = Annotated[Ticker, Query(description="Currency ticker")]


@router.get("", response_model=list[PriceRead], summary="All stored prices")
async def get_prices(service: PriceServiceDep, ticker: TickerQuery) -> list:
    return await service.get_all(ticker)


@router.get("/latest", response_model=PriceRead, summary="Latest price")
async def get_latest_price(service: PriceServiceDep, ticker: TickerQuery):
    return await service.get_latest(ticker)


@router.get("/filter", response_model=list[PriceRead], summary="Prices by date range")
async def get_prices_by_date(
    service: PriceServiceDep,
    ticker: TickerQuery,
    date_from: Annotated[
        int | None, Query(ge=0, description="Start of range, UNIX timestamp")
    ] = None,
    date_to: Annotated[
        int | None, Query(ge=0, description="End of range, UNIX timestamp")
    ] = None,
) -> list:
    return await service.get_by_date_range(ticker, date_from, date_to)
