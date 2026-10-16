from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str

    deribit_base_url: str = "https://www.deribit.com/api/v2"
    deribit_request_timeout: int = 10

    price_collection_interval: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
