"""
FastMCP Production Server — Entry Point
"""

from contextlib import asynccontextmanager

from fastmcp import FastMCP

from .config.security import initialize_allowlist
from .config.settings import Settings
from .db.connection import DatabasePool
from .db.pool import set_pool
from .observability.telemetry import setup_telemetry
from .tools import health, search, detail, stats

settings = Settings()
telemetry = setup_telemetry(settings.service_name)
db_pool = DatabasePool(
    dsn=settings.database_url,
    min_size=settings.db_pool_min,
    max_size=settings.db_pool_max,
)


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Initialize and teardown resources."""
    initialize_allowlist(settings.allowlist_path)
    await db_pool.initialize()
    set_pool(db_pool)  # make pool available to tools via singleton
    yield
    await db_pool.close()


mcp = FastMCP(
    name=settings.service_name,
    instructions=settings.service_description,
    lifespan=lifespan,
)

# Register tools
mcp.add_tool(search.search_records)
mcp.add_tool(detail.get_record_detail)
mcp.add_tool(stats.get_statistics)
mcp.add_tool(health.get_pool_status)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=settings.port)
