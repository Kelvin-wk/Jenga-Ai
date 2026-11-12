"""FastAPI application composition."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, catalog, chat, conversations, media, reviews
from app.db.database import init_db
from app.schemas.common import HealthResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Jenga Consultants Product Copilot", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(catalog.router)
app.include_router(media.router)
app.include_router(conversations.router)
app.include_router(reviews.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(catalog.router, prefix="/api/v1")
app.include_router(media.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc))


@app.get("/api/v1/health", response_model=HealthResponse, tags=["health"])
def versioned_health() -> HealthResponse:
    return health()


@app.get("/ready", tags=["health"])
def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/api/v1/ready", tags=["health"])
def versioned_ready() -> dict[str, str]:
    return ready()
