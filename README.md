# fastmcp-production-template

> Production-ready MCP server template with async PostgreSQL, OpenTelemetry, tool-level security allowlisting, Docker, and Kubernetes Helm chart. Zero to deployed in 10 minutes.

[![CI](https://github.com/ManjunathGovindaraju/fastmcp-production-template/actions/workflows/ci.yml/badge.svg)](https://github.com/ManjunathGovindaraju/fastmcp-production-template/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.x-green.svg)](https://github.com/jlowin/fastmcp)

Most MCP server examples are toy demos — a few tools, no database, no auth, no observability. The moment you try to deploy one in production you hit the same set of problems:

- How do I manage a database connection pool safely across async tool calls?
- How do I prevent prompt injection via unauthorized tool invocation?
- How do I get distributed traces into my existing observability stack?
- How do I deploy this to Kubernetes with proper secrets management?

This template solves all of that. Fork it, rename it, and ship your MCP server.

## Features

| Feature | Implementation |
|---|---|
| Async PostgreSQL | `asyncpg` connection pool (min 5, max 20), parameterized queries |
| OpenTelemetry | Traces, custom metrics (`tool.calls`, `tool.errors`, `tool.duration`, `db.pool_size`) |
| Security allowlist | YAML-based tool allowlist prevents unauthorized tool invocation |
| Docker | Multi-stage build, non-root user, health check |
| Kubernetes | Helm chart, HPA (2–8 replicas), External Secrets Operator, ADOT sidecar |
| CI/CD | GitHub Actions: Ruff lint → pytest → Docker build |
| Configuration | Pydantic Settings, `.env` based, 12-factor compliant |

## Quick Start

### Option 1: Docker Compose (2 minutes)

```bash
git clone https://github.com/ManjunathGovindaraju/fastmcp-production-template.git
cd fastmcp-production-template
cp .env.example .env
docker compose -f docker/docker-compose.yml up
```

The MCP server starts on `http://localhost:8000`. PostgreSQL starts with sample data loaded from `docker/init.sql`.

### Option 2: Local Python

```bash
git clone https://github.com/ManjunathGovindaraju/fastmcp-production-template.git
cd fastmcp-production-template

# Install uv if needed: https://docs.astral.sh/uv/
uv sync

cp .env.example .env
# Edit .env with your PostgreSQL connection string

uv run python -m server.main
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client (LLM)                     │
└──────────────────────────┬──────────────────────────────┘
                           │ Streamable HTTP / SSE
┌──────────────────────────▼──────────────────────────────┐
│                   FastMCP Server                        │
│                                                         │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────┐  │
│  │  Allowlist  │   │ OpenTelemetry│   │   Settings  │  │
│  │  Security   │   │  Telemetry   │   │  (Pydantic) │  │
│  └──────┬──────┘   └──────┬───────┘   └─────────────┘  │
│         │                 │                             │
│  ┌──────▼─────────────────▼───────────────────────────┐ │
│  │                    Tools                           │ │
│  │  search_records │ get_record_detail │ get_statistics│ │
│  └──────────────────────────┬──────────────────────── ┘ │
│                             │                           │
│  ┌──────────────────────────▼───────────────────────┐   │
│  │           DatabasePool (asyncpg)                 │   │
│  │     connection pool · parameterized queries      │   │
│  └──────────────────────────┬───────────────────────┘   │
└─────────────────────────────│───────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │    PostgreSQL      │
                    │  (asyncpg pool)    │
                    └───────────────────┘
```

## Security Model

Tool invocations are gated by a YAML allowlist loaded at startup. Any tool not on the list raises `PermissionError` before execution — this prevents prompt injection attacks where a malicious prompt attempts to invoke an internal or debugging tool.

```yaml
# config/allowlist.yaml
allowed_tools:
  - search_records
  - get_record_detail
  - get_statistics
```

```python
@require_allowlist("search_records")
async def search_records(query: str, limit: int = 10) -> list[dict]:
    ...
```

The `get_pool_status` health tool bypasses the allowlist intentionally — health checks must always be reachable.

SQL injection is prevented by two mechanisms:
1. All user-supplied values use `asyncpg` parameterized queries (`$1`, `$2`)
2. `get_statistics` validates `group_by` against a hardcoded set of allowed column names before query construction

## Observability

OpenTelemetry traces and metrics export to any OTLP-compatible backend (Jaeger, Grafana Tempo, AWS X-Ray via ADOT, Datadog).

| Metric | Type | Description |
|---|---|---|
| `mcp.tool.calls` | Counter | Total tool invocations, labeled by `tool_name` |
| `mcp.tool.errors` | Counter | Failed invocations, labeled by `tool_name` |
| `mcp.tool.duration` | Histogram | End-to-end latency per tool call |
| `mcp.db.pool_size` | Gauge | Live asyncpg connection pool size |

Configure the exporter endpoint in `.env`:

```bash
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=fastmcp-production-template
```

## Kubernetes Deployment

```bash
# Install with Helm
helm install fastmcp-server k8s/helm/ \
  --set image.repository=your-registry/fastmcp-production-template \
  --set image.tag=1.0.0 \
  --namespace mcp-system \
  --create-namespace

# Scale
kubectl scale deployment fastmcp-server --replicas=4 -n mcp-system

# Check HPA
kubectl get hpa -n mcp-system
```

The Helm chart includes:
- HPA: scales 2–8 replicas at 70% CPU
- External Secrets Operator integration (pulls `DATABASE_URL`, `API_KEY` from Vault)
- ADOT sidecar annotation support for AWS X-Ray
- Non-root security context (`runAsNonRoot: true`)
- ConfigMap mount for `allowlist.yaml`

## Project Structure

```
fastmcp-production-template/
├── src/server/
│   ├── main.py                  # FastMCP entry point, lifespan hooks
│   ├── config/
│   │   ├── settings.py          # Pydantic Settings (env / .env)
│   │   └── security.py          # Allowlist loader and @require_allowlist decorator
│   ├── db/
│   │   └── connection.py        # asyncpg DatabasePool with fetch/execute helpers
│   ├── observability/
│   │   └── telemetry.py         # OpenTelemetry setup, custom metrics
│   └── tools/
│       ├── search.py            # search_records tool
│       ├── detail.py            # get_record_detail tool
│       ├── stats.py             # get_statistics tool
│       └── health.py            # get_pool_status tool
├── config/
│   └── allowlist.yaml           # Tool allowlist
├── docker/
│   ├── Dockerfile               # Multi-stage build
│   ├── docker-compose.yml       # MCP server + PostgreSQL
│   └── init.sql                 # Sample schema and data
├── k8s/helm/
│   ├── values.yaml              # Helm values (HPA, ESO, ADOT)
│   └── templates/
│       └── deployment.yaml      # K8s Deployment with security context
├── tests/
│   ├── test_security.py         # Allowlist enforcement tests
│   └── test_tools.py            # Tool behavior and SQL injection prevention
├── .github/workflows/
│   └── ci.yml                   # Ruff + pytest + Docker build
├── pyproject.toml               # uv/hatch project config
└── .env.example                 # Configuration reference
```

## Extending This Template

Adding a new tool takes three steps:

**1. Create the tool function** in `src/server/tools/your_tool.py`:

```python
from ..config.security import require_allowlist
from ..db.connection import db_pool

@require_allowlist("your_tool_name")
async def your_tool_name(param: str) -> dict:
    row = await db_pool.fetchrow("SELECT * FROM your_table WHERE id = $1", param)
    return dict(row) if row else {}
```

**2. Register it** in `src/server/main.py`:

```python
from .tools import your_tool
mcp.add_tool(your_tool.your_tool_name)
```

**3. Add it to the allowlist** in `config/allowlist.yaml`:

```yaml
allowed_tools:
  - your_tool_name
```

## Running Tests

```bash
uv run pytest tests/ -v
```

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `SERVICE_NAME` | `fastmcp-production-template` | MCP server name |
| `PORT` | `8000` | Uvicorn listen port |
| `DATABASE_URL` | — | asyncpg DSN (`postgresql://user:pass@host/db`) |
| `DB_POOL_MIN` | `5` | Minimum pool connections |
| `DB_POOL_MAX` | `20` | Maximum pool connections |
| `ALLOWLIST_PATH` | `config/allowlist.yaml` | Path to tool allowlist |
| `API_KEY_ENABLED` | `true` | Enable API key auth |
| `API_KEY` | — | Bearer token for requests |
| `OTEL_ENABLED` | `true` | Enable OpenTelemetry export |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP collector endpoint |

## Author

**Manjunath Govindaraju** — Principal Software Engineer with 23 years building production systems. Currently focused on AI platform engineering: multi-agent orchestration (LangGraph), MCP servers, async data pipelines, and enterprise Kubernetes deployments.

[LinkedIn](https://www.linkedin.com/in/manjunathgovindaraju/) · [GitHub](https://github.com/ManjunathGovindaraju)

## License

MIT — fork freely, use in production, no attribution required.
