"""GET /health – database, redis, imap, queue status."""

import logging
from datetime import datetime

from backend.app.core.deps import RedisDep, SessionDep
from backend.app.schemas.health import HealthResponse
from fastapi import APIRouter
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(session: SessionDep, redis: RedisDep) -> HealthResponse:
    # --- Database ---
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Database health-check failed")
        db_status = "error"

    # --- Redis ---
    redis_status = "ok"
    try:
        if redis is None:
            redis_status = "error"
        else:
            await redis.ping()
    except Exception:
        logger.exception("Redis health-check failed")
        redis_status = "error"

    # --- IMAP last poll (M10 §4.9: key imap:last_poll) ---
    imap_last_poll: datetime | None = None
    if redis is not None:
        try:
            raw = await redis.get("imap:last_poll")
            if raw:
                imap_last_poll = datetime.fromisoformat(raw.decode() if isinstance(raw, bytes) else raw)
        except Exception:
            logger.warning("Could not read imap:last_poll from Redis")

    # --- Queue depth (M10 §4.9: key queue:depth) ---
    queue_depth = 0
    if redis is not None:
        try:
            raw_depth = await redis.get("queue:depth")
            if raw_depth:
                queue_depth = int(raw_depth)
        except Exception:
            logger.warning("Could not read queue:depth from Redis")

    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    return HealthResponse(
        status=overall,
        database=db_status,
        redis=redis_status,
        imap_last_poll=imap_last_poll,
        queue_depth=queue_depth,
    )
