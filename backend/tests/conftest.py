"""Shared test fixtures – async client against the FastAPI app."""

import contextlib
import os
from collections.abc import AsyncGenerator

import pytest
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient

# Provide safe environment defaults for testing
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://sam:sam@localhost:5432/ticketing_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")

from backend.app.core.config import settings  # noqa: E402
from backend.app.main import create_app  # noqa: E402


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client wired to the FastAPI app."""
    app = create_app()

    # Initialize a test redis pool on app state
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
    app.state.redis = redis_client

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    with contextlib.suppress(Exception):
        await redis_client.aclose()
