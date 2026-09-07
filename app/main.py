import logging
from fastapi import FastAPI
from opentelemetry import trace

from app.api.v1.job_board.job_board import router as job_board_router
from app.core.logging import configure_logging
from app.middleware.request_context import request_context_middleware
from app.infrastructure.observability.tracing import (
    configure_tracing,
)
from opentelemetry.instrumentation.fastapi import (
    FastAPIInstrumentor,
)
from opentelemetry.instrumentation.requests import (
    RequestsInstrumentor,
)
from app.infrastructure.observability.tracing import configure_otel_logging, configure_metrics

configure_logging()
configure_tracing()
configure_otel_logging()
configure_metrics()

logger = logging.getLogger(__name__)

app = FastAPI()

app.middleware("http")(request_context_middleware)
app.include_router(router=job_board_router)

FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()


@app.get("/health")
def health():
    logger.info("Server is healthy")
    return {"status": "Healthy"}

