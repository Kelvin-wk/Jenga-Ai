"""Catalog routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.common import ProductResponse
from app.tools.catalog import lookup_products

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/products", response_model=list[ProductResponse])
def list_products(db: Annotated[Session, Depends(get_db)]) -> list[ProductResponse]:
    return [ProductResponse.model_validate(product, from_attributes=True) for product in lookup_products(db)]
