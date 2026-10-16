import asyncio
import logging

from app.clients.deribit_client import DeribitClient, DeribitClientError
from app.core.config import get_settings
from app.core.database import Database
from app.repositories.price_repository import PriceRepository
from app.services.price_service import PriceService
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _collect_prices() -> list[str]:
    settings = get_settings()
    # Every run owns its event loop, so pooled connections cannot be reused between runs.
    database = Database(settings.database_url, use_null_pool=True)
    try:
        async with database.session() as session:
            async with DeribitClient(
                settings.deribit_base_url, settings.deribit_request_timeout
            ) as client:
                service = PriceService(PriceRepository(session), client)
                prices = await service.collect_all()
                return [f"{price.ticker}={price.price}" for price in prices]
    finally:
        await database.dispose()


@celery_app.task(
    name="app.tasks.price_tasks.collect_prices",
    autoretry_for=(DeribitClientError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def collect_prices() -> list[str]:
    collected = asyncio.run(_collect_prices())
    logger.info("Collected prices: %s", ", ".join(collected))
    return collected
