"""
OpenTelemetry setup for MCP server observability.
Provides distributed tracing and metrics for all tool calls.
"""

import logging
import os
from dataclasses import dataclass

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

logger = logging.getLogger(__name__)


@dataclass
class Telemetry:
    tracer: trace.Tracer
    tool_calls: metrics.Counter
    tool_errors: metrics.Counter
    tool_duration: metrics.Histogram
    db_pool_size: metrics.ObservableGauge


def setup_telemetry(service_name: str) -> Telemetry:
    """
    Initialize OpenTelemetry tracing and metrics.
    Supports OTLP export (production) and console export (local dev).
    """
    resource = Resource.create({"service.name": service_name})

    # Tracing
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    # Metrics
    metric_reader = PeriodicExportingMetricReader(
        ConsoleMetricExporter(), export_interval_millis=30000
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    tracer = trace.get_tracer(service_name)
    meter = metrics.get_meter(service_name)

    logger.info(f"OpenTelemetry initialized for service: {service_name}")

    return Telemetry(
        tracer=tracer,
        tool_calls=meter.create_counter(
            "mcp.tool.calls",
            description="Total number of MCP tool invocations",
        ),
        tool_errors=meter.create_counter(
            "mcp.tool.errors",
            description="Total number of MCP tool errors",
        ),
        tool_duration=meter.create_histogram(
            "mcp.tool.duration",
            unit="ms",
            description="MCP tool execution duration in milliseconds",
        ),
        db_pool_size=meter.create_observable_gauge(
            "mcp.db.pool_size",
            description="Current DB connection pool size",
        ),
    )
