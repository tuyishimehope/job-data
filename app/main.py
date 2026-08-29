from fastapi import FastAPI

from app.api.v1.job_board.job_board import router as job_board_router
from app.core.logging import configure_logging
from app.middleware.request_context import request_context_middleware
import logging

logger = logging.getLogger(__name__)

configure_logging()

app = FastAPI()

app.include_router(router=job_board_router)


app.middleware("http")(request_context_middleware)


@app.get("/health")
def health():
    logger.info("Server is healthy")
    return {"status": "Healthy"}
