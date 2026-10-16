from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Ticker(StrEnum):
    BTC_USD = "btc_usd"
    ETH_USD = "eth_usd"


class PriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    price: Decimal
    timestamp: int
