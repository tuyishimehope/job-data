from fastapi import FastAPI

from app.api.v1.job_board.job_board import router as job_board_router
from app.core.logging import configure_logging

configure_logging()

app = FastAPI()

app.include_router(router=job_board_router)


@app.get("/health")
def health():
    return {"status": "Healthy"}
