"""FastAPI dependencies: async DB session, Redis connection."""

from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as aioredis
from backend.app.db.session import async_session_factory
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield one async session per request, then close."""
    async with async_session_factory() as session:
        yield session


def get_redis(request: Request) -> aioredis.Redis | None:
    """Return the Redis connection pool stored on app state, if any."""
    return getattr(request.app.state, "redis", None)


SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]
