"""ARQ worker entrypoint and heartbeat cron job.

Start with:  arq backend.app.workers.worker.WorkerSettings
"""

import logging
from datetime import UTC, datetime

from arq import cron
from arq.connections import RedisSettings
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def _redis_settings() -> RedisSettings:
    """Parse REDIS_URL into ARQ's RedisSettings."""
    from urllib.parse import urlparse

    parsed = urlparse(settings.REDIS_URL)
    return RedisSettings(
        host=parsed.hostname or "redis",
        port=parsed.port or 6379,
        database=int(parsed.path.lstrip("/") or 0),
        password=parsed.password,
    )


async def heartbeat(ctx: dict) -> None:  # type: ignore[type-arg]
    """Write worker heartbeat timestamp to Redis."""
    redis = ctx["redis"]
    now = datetime.now(UTC).isoformat()
    await redis.set("status:worker_heartbeat", now)
    logger.debug("Worker heartbeat: %s", now)


# ---------------------------------------------------------------------------
# Register module jobs here.
#
# To add a new job, import the function and append to `functions`:
#
#   from backend.app.pipeline.runner import process_email
#   functions = [process_email, ...]
#
# To add a new cron job, append to `cron_jobs`:
#
#   cron(check_ack_timeouts, second={0, 30}),
# ---------------------------------------------------------------------------


class WorkerSettings:
    """ARQ worker configuration."""

    redis_settings = _redis_settings()

    functions: list = []  # populated by module registrations above

    cron_jobs = [
        cron(heartbeat, second={0, 30}),  # every 30 seconds
    ]

    max_jobs = 10
    job_timeout = 300  # 5 minutes default
