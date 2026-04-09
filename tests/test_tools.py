"""
Tests for MCP tool functions.
Uses pytest-asyncio for async test support.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.server.tools.health import get_pool_status
from src.server.tools.stats import get_statistics


@pytest.fixture
def mock_ctx():
    """Mock FastMCP context with a fake DB pool."""
    ctx = MagicMock()
    ctx.server.db_pool = AsyncMock()
    ctx.server.db_pool.health_check = AsyncMock(return_value={
        "status": "healthy", "size": 5, "idle": 3,
        "min_size": 5, "max_size": 20,
    })
    return ctx


@pytest.mark.asyncio
async def test_get_pool_status_returns_healthy(mock_ctx):
    result = await get_pool_status(mock_ctx)
    assert result["server"] == "healthy"
    assert result["database"]["status"] == "healthy"
    assert result["database"]["size"] == 5


@pytest.mark.asyncio
async def test_get_statistics_invalid_group_by_raises(mock_ctx):
    with pytest.raises(ValueError, match="Invalid group_by field"):
        await get_statistics(mock_ctx, group_by="injected_field; DROP TABLE records;--")


@pytest.mark.asyncio
async def test_get_statistics_valid_group_by(mock_ctx):
    mock_ctx.server.db_pool.fetch = AsyncMock(return_value=[
        {"label": "active", "count": 42},
        {"label": "inactive", "count": 8},
    ])
    with patch("src.server.config.security.is_allowed", return_value=True):
        result = await get_statistics(mock_ctx, group_by="status")
    assert result["total"] == 50
    assert result["group_by"] == "status"
    assert len(result["breakdown"]) == 2
