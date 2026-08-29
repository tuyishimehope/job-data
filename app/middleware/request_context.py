import logging
from uuid import uuid4
from time import perf_counter
from fastapi import  Request
from app.core.context import request_id_context

logger = logging.getLogger(__name__)


async def request_context_middleware(
    request: Request,
    call_next,
):
    request_id = (
        request.headers.get("X-Request-ID")
        or str(uuid4())
    )

    token = request_id_context.set(request_id)

    start_time = perf_counter()

    logger.info(
        "HTTP request started",
        extra={
            "event": "http_request_started",
            "http_method": request.method,
            "http_path": request.url.path,
        },
    )

    try:
        response = await call_next(request)

        duration_ms = (
            perf_counter() - start_time
        ) * 1000

        logger.info(
            "HTTP request completed",
            extra={
                "event": "http_request_completed",
                "http_method": request.method,
                "http_path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

        response.headers["X-Request-ID"] = request_id

        return response

    except Exception:
        duration_ms = (
            perf_counter() - start_time
        ) * 1000

        logger.exception(
            "HTTP request failed",
            extra={
                "event": "http_request_failed",
                "http_method": request.method,
                "http_path": request.url.path,
                "duration_ms": round(duration_ms, 2),
            },
        )

        raise

    finally:
        request_id_context.reset(token)
