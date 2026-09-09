import logging

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.settings import settings


def configure_tracing() -> None:
    resource = Resource.create(
        {
            SERVICE_NAME: settings.app_name,
            "deployment.environment.name": settings.environment,
        }
    )

    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint="https://otlp.nr-data.net/v1/traces",
        headers={
            "api-key": settings.NEW_RELIC_LICENSE_KEY,
        },
    )

    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)


def configure_otel_logging() -> None:
    resource = Resource.create(
        {
            SERVICE_NAME: settings.app_name,
            "deployment.environment.name": settings.environment,
        }
    )

    logger_provider = LoggerProvider(resource=resource)

    exporter = OTLPLogExporter(
        endpoint="https://otlp.nr-data.net/v1/logs",
        headers={
            "api-key": settings.NEW_RELIC_LICENSE_KEY,
            "protocol": settings.OTEL_EXPORTER_OTLP_PROTOCOL,
        },
    )

    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

    set_logger_provider(logger_provider)

    handler = LoggingHandler(
        level=logging.INFO,
        logger_provider=logger_provider,
    )

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)


def configure_metrics() -> None:
    resource = Resource.create(
        {
            SERVICE_NAME: settings.app_name,
            "deployment.environment.name": settings.environment,
        }
    )

    exporter = OTLPMetricExporter(
        endpoint="https://otlp.nr-data.net/v1/metrics",
        headers={
            "api-key": settings.NEW_RELIC_LICENSE_KEY,
        },
    )

    reader = PeriodicExportingMetricReader(
        exporter,
        export_interval_millis=5000,
    )

    provider = MeterProvider(
        resource=resource,
        metric_readers=[reader],
    )

    metrics.set_meter_provider(provider)
