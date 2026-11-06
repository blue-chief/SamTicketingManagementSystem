"""Smoke tests for GET /health."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert data["database"] in ("ok", "error")
    assert data["redis"] in ("ok", "error")
    assert "imap_last_poll" in data
    assert "queue_depth" in data


@pytest.mark.asyncio
async def test_health_schema_fields(client: AsyncClient) -> None:
    resp = await client.get("/health")
    data = resp.json()
    expected_fields = {"status", "database", "redis", "imap_last_poll", "queue_depth"}
    assert set(data.keys()) == expected_fields


@pytest.mark.asyncio
async def test_health_queue_depth_is_int(client: AsyncClient) -> None:
    resp = await client.get("/health")
    data = resp.json()
    assert isinstance(data["queue_depth"], int)
