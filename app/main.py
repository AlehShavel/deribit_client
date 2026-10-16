from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routers import prices
from app.clients.deribit_client import DeribitClient
from app.core.config import Settings, get_settings
from app.core.database import Database
from app.services.price_service import PriceNotFoundError


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.database = Database(settings.database_url)
        app.state.deribit_client = DeribitClient(
            settings.deribit_base_url, settings.deribit_request_timeout
        )
        try:
            yield
        finally:
            await app.state.deribit_client.close()
            await app.state.database.dispose()

    app = FastAPI(title="Deribit Prices API", lifespan=lifespan)
    app.state.settings = settings
    app.include_router(prices.router)

    @app.exception_handler(PriceNotFoundError)
    async def handle_price_not_found(
        request: Request, exc: PriceNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    return app


app = create_app()
