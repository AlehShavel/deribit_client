from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price import Price


class PriceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, ticker: str, price: Decimal, timestamp: int) -> Price:
        record = Price(ticker=ticker, price=price, timestamp=timestamp)
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def get_all(self, ticker: str) -> list[Price]:
        query = (
            select(Price).where(Price.ticker == ticker).order_by(Price.timestamp.desc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_latest(self, ticker: str) -> Price | None:
        query = (
            select(Price)
            .where(Price.ticker == ticker)
            .order_by(Price.timestamp.desc())
            .limit(1)
        )
        result = await self._session.execute(query)
        return result.scalars().first()

    async def get_by_date_range(
        self,
        ticker: str,
        date_from: int | None = None,
        date_to: int | None = None,
    ) -> list[Price]:
        query = select(Price).where(Price.ticker == ticker)
        if date_from is not None:
            query = query.where(Price.timestamp >= date_from)
        if date_to is not None:
            query = query.where(Price.timestamp <= date_to)
        result = await self._session.execute(query.order_by(Price.timestamp.desc()))
        return list(result.scalars().all())
