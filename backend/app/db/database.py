"""SQLite database setup, ORM models, and deterministic seed data."""

from __future__ import annotations

import os
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Generator

from passlib.context import CryptContext
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jenga_consultants.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
# PBKDF2 avoids the known passlib/bcrypt backend incompatibility while retaining
# passlib's constant-time verification and configurable work factor.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class UserDB(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ProductDB(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    specifications: Mapped[str] = mapped_column(String(2000), nullable=False)
    price_ksh: Mapped[int] = mapped_column(Integer, nullable=False)


class AuditLogDB(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_role: Mapped[str] = mapped_column(String(32), nullable=False)
    tool_used: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)


class SessionDB(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)


class ConversationDB(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)


class MediaDB(Base):
    __tablename__ = "media"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ReviewRequestDB(Base):
    __tablename__ = "review_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="submitted", nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped database session."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables and insert idempotent development seed data."""

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(UserDB).where(UserDB.username == "engineer@jenga.com")) is None:
            db.add_all(
                [
                    UserDB(
                        username="engineer@jenga.com",
                        hashed_password=pwd_context.hash("engineer123"),
                        role="engineer",
                    ),
                    UserDB(
                        username="customer@jenga.com",
                        hashed_password=pwd_context.hash("customer123"),
                        role="customer",
                    ),
                ]
            )
        if db.scalar(select(ProductDB).where(ProductDB.model_number == "JCG-1000")) is None:
            db.add_all(
                [
                    ProductDB(
                        category="generator",
                        name="Jenga Genset 1000",
                        model_number="JCG-1000",
                        specifications="1000 kVA, diesel, automatic transfer switch",
                        price_ksh=12500000,
                    ),
                    ProductDB(
                        category="transformer",
                        name="Jenga Dry-Type Transformer",
                        model_number="JCT-500",
                        specifications="500 kVA, 11/0.415 kV, low-noise enclosure",
                        price_ksh=3850000,
                    ),
                    ProductDB(
                        category="solar",
                        name="Jenga Solar Inverter",
                        model_number="JCS-50",
                        specifications="50 kW three-phase hybrid inverter",
                        price_ksh=875000,
                    ),
                ]
            )
        db.commit()


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for audit records."""

    return datetime.now(timezone.utc)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
