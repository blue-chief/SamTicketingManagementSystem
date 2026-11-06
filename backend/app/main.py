"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from backend.app.api.health import router as health_router
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup: init Redis pool.  Shutdown: close it."""
    setup_logging()
    logger.info("Starting up – connecting to Redis")
    app.state.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
    yield
    logger.info("Shutting down – closing Redis")
    await app.state.redis.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="SamConsultingFirm Ticket Management",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.APP_BASE_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router)

    return app


app = create_app()
