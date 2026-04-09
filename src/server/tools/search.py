"""
search_records — Generic search tool with filtering, pagination, and observability.
"""

import logging
import time
from typing import Any

from fastmcp import Context

from ..config.security import require_allowlist
from ..db.connection import DatabasePool

logger = logging.getLogger(__name__)


@require_allowlist("search_records")
async def search_records(
    ctx: Context,
    query: str,
    limit: int = 20,
    offset: int = 0,
    filters: dict[str, Any] | None = None,
) -> dict:
    """
    Search records using a full-text query with optional field filters.

    Args:
        query: Search term to match against record fields
        limit: Maximum number of results to return (default: 20, max: 100)
        offset: Pagination offset (default: 0)
        filters: Optional key-value pairs for exact field matching

    Returns:
        Dictionary with 'results' list and 'total' count
    """
    start = time.monotonic()
    limit = min(limit, 100)  # enforce max page size

    db: DatabasePool = ctx.server.db_pool

    try:
        # Build parameterized query — never use string interpolation
        where_clauses = ["(name ILIKE $1 OR description ILIKE $1)"]
        params: list[Any] = [f"%{query}%"]

        if filters:
            for i, (col, val) in enumerate(filters.items(), start=2):
                where_clauses.append(f"{col} = ${i}")
                params.append(val)

        where_sql = " AND ".join(where_clauses)
        sql = f"""
            SELECT id, name, description, status, created_at
            FROM records
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """
        params.extend([limit, offset])

        count_sql = f"SELECT COUNT(*) FROM records WHERE {where_sql}"
        count_params = params[: len(params) - 2]

        results, total = await asyncio.gather(
            db.fetch(sql, *params),
            db.fetchval(count_sql, *count_params),
        )

        duration_ms = (time.monotonic() - start) * 1000
        logger.info(f"search_records: query='{query}' results={len(results)} total={total} duration={duration_ms:.1f}ms")

        return {
            "results": results,
            "total": total,
            "limit": limit,
            "offset": offset,
            "query": query,
        }

    except Exception as e:
        logger.error(f"search_records failed: {e}")
        raise
