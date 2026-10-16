from celery import Celery

from app.core.config import Settings, get_settings


def create_celery_app(settings: Settings | None = None) -> Celery:
    settings = settings or get_settings()
    celery_app = Celery(
        "prices",
        broker=settings.redis_url,
        include=["app.tasks.price_tasks"],
    )
    celery_app.conf.update(
        timezone="UTC",
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        beat_schedule={
            "collect-prices": {
                "task": "app.tasks.price_tasks.collect_prices",
                "schedule": float(settings.price_collection_interval),
            }
        },
    )
    return celery_app


celery_app = create_celery_app()
