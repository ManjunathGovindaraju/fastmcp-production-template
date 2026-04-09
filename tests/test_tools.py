"""
Tests for MCP tool functions.
Uses pytest-asyncio for async test support.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.server.tools.health import get_pool_status
from src.server.tools.stats import get_statistics


@pytest.fixture
def mock_pool():
    """Mock DatabasePool for unit tests."""
    pool = AsyncMock()
    pool.health_check = AsyncMock(return_value={
        "status": "healthy", "size": 5, "idle": 3,
        "min_size": 5, "max_size": 20,
    })
    return pool


@pytest.mark.asyncio
async def test_get_pool_status_returns_healthy(mock_pool):
    with patch("src.server.tools.health.get_pool", return_value=mock_pool):
        result = await get_pool_status()
    assert result["server"] == "healthy"
    assert result["database"]["status"] == "healthy"
    assert result["database"]["size"] == 5


@pytest.mark.asyncio
async def test_get_statistics_invalid_group_by_raises():
    with patch("src.server.config.security.is_allowed", return_value=True):
        with pytest.raises(ValueError, match="Invalid group_by field"):
            await get_statistics(group_by="injected_field; DROP TABLE records;--")


@pytest.mark.asyncio
async def test_get_statistics_valid_group_by(mock_pool):
    mock_pool.fetch = AsyncMock(return_value=[
        {"label": "active", "count": 42},
        {"label": "inactive", "count": 8},
    ])
    with patch("src.server.tools.stats.get_pool", return_value=mock_pool):
        with patch("src.server.config.security.is_allowed", return_value=True):
            result = await get_statistics(group_by="status")
    assert result["total"] == 50
    assert result["group_by"] == "status"
    assert len(result["breakdown"]) == 2
