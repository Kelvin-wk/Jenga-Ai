"""Catalog routes."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import ProductDB, get_db
from app.schemas.catalogue import CompareRequest, CompareResponse, PriceLineItem, PriceRequest, PriceResponse
from app.schemas.common import ProductResponse
from app.tools.catalog import lookup_products

router = APIRouter(prefix="/catalogue", tags=["catalogue"])


@router.get("/products", response_model=list[ProductResponse])
def list_products(db: Annotated[Session, Depends(get_db)]) -> list[ProductResponse]:
    return [ProductResponse.model_validate(product, from_attributes=True) for product in lookup_products(db)]


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Annotated[Session, Depends(get_db)]) -> ProductResponse:
    product = db.get(ProductDB, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product, from_attributes=True)


@router.post("/price", response_model=PriceResponse)
def calculate_price(
    payload: PriceRequest,
    db: Annotated[Session, Depends(get_db)],
) -> PriceResponse:
    line_items: list[PriceLineItem] = []
    subtotal = 0
    for product_id, quantity in payload.items:
        if quantity <= 0:
            raise HTTPException(status_code=422, detail="Quantities must be positive")
        product = db.get(ProductDB, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        line_total = product.price_ksh * 100 * quantity
        subtotal += line_total
        line_items.append(
            PriceLineItem(
                product_id=product.id,
                model_number=product.model_number,
                quantity=quantity,
                unit_price_minor=product.price_ksh * 100,
                line_total_minor=line_total,
            )
        )
    tax = subtotal * (payload.tax_rate_bps or 0) // 10000
    return PriceResponse(
        line_items=line_items,
        subtotal_minor=subtotal,
        tax_minor=tax,
        total_minor=subtotal + tax,
        price_date=datetime.now(timezone.utc).date(),
        source_row_ids=[f"product:{item.product_id}" for item in line_items],
    )


@router.post("/compare", response_model=CompareResponse)
def compare_products(
    payload: CompareRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CompareResponse:
    products = [db.get(ProductDB, product_id) for product_id in payload.product_ids]
    if any(product is None for product in products):
        raise HTTPException(status_code=404, detail="Product not found")
    fields = payload.fields or ["category", "model_number", "specifications", "price_ksh"]
    return CompareResponse(
        products=[
            {"id": product.id, **{field: getattr(product, field, None) for field in fields}}
            for product in products
            if product is not None
        ],
        fields=fields,
    )
