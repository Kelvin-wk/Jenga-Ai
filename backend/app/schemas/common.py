"""Common API schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    timestamp: datetime


class ProductResponse(BaseModel):
    id: int
    category: str
    name: str
    model_number: str
    specifications: str
    price_ksh: int
