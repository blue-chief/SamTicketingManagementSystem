"""Health-check response schema."""

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str
    imap_last_poll: datetime | None
    queue_depth: int
