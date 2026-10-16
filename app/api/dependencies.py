from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.deribit_client import DeribitClient
from app.core.database import Database
from app.repositories.price_repository import PriceRepository
from app.services.price_service import PriceService


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_client(request: Request) -> DeribitClient:
    return request.app.state.deribit_client


async def get_session(
    database: Annotated[Database, Depends(get_database)],
) -> AsyncIterator[AsyncSession]:
    async with database.session() as session:
        yield session


def get_price_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    client: Annotated[DeribitClient, Depends(get_client)],
) -> PriceService:
    return PriceService(PriceRepository(session), client)


PriceServiceDep = Annotated[PriceService, Depends(get_price_service)]
