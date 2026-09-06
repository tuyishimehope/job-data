from time import perf_counter

from fastapi import FastAPI, Request

from app.api.v1.job_board.job_board import router as job_board_router
from app.core.gauge import Gauge
from app.core.histogram import Histogram
from app.core.logging import configure_logging
from app.core.metrics import Counter
from app.middleware.request_context import request_context_middleware
import logging

logger = logging.getLogger(__name__)

configure_logging()

app = FastAPI()

app.include_router(router=job_board_router)


app.middleware("http")(request_context_middleware)

# http_requests_total = Counter()
# active_http_requests = Gauge()
# http_request_duration_ms = Histogram([])


# @app.middleware("http")
# async def request_context_middleware(
#     request: Request,
#     call_next,
# ):

#     active_http_requests.increment()
#     start_time = perf_counter()

#     try:
#         response = await call_next(request)
#         duration_ms = (
#             perf_counter() - start_time
#         ) * 1000
#         http_requests_total.increment(
#             labels=(request.method, response.status_code))
#         http_request_duration_ms.observe(
#             duration_ms
#         )

#         return response

#     finally:
#         active_http_requests.decrement()


@app.get("/health")
def health():
    logger.info("Server is healthy")
    return {"status": "Healthy"}

