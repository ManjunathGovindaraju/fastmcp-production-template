"""
FastMCP Production Server — Entry Point
"""

from contextlib import asynccontextmanager

from fastmcp import FastMCP

from .config.settings import Settings
from .db.connection import DatabasePool
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
    await db_pool.initialize()
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
    import uvicorn
    uvicorn.run("src.server.main:mcp", host="0.0.0.0", port=settings.port, reload=False)
