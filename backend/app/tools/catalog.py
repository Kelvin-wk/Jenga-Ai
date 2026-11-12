"""Catalog lookup tool."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import ProductDB


def lookup_products(db: Session) -> list[ProductDB]:
    return list(db.scalars(select(ProductDB).order_by(ProductDB.name)).all())
