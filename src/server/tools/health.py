"""
get_pool_status — Health check tool exposing DB pool and server status.
"""

import logging

from fastmcp import Context

from ..db.connection import DatabasePool

logger = logging.getLogger(__name__)


async def get_pool_status(ctx: Context) -> dict:
    """
    Return current database connection pool status and server health.
    Not subject to allowlist — always accessible for monitoring.

    Returns:
        Pool size, idle connections, and overall health status
    """
    db: DatabasePool = ctx.server.db_pool
    pool_status = await db.health_check()
    logger.debug(f"get_pool_status: {pool_status}")
    return {"server": "healthy", "database": pool_status}
