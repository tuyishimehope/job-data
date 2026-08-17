from pydantic import BaseModel, ConfigDict


class GreenhouseLocation(BaseModel):
    name: str


class GreenhouseJob(BaseModel):
    id: int
    internal_job_id: int | None = None
    title: str
    updated_at: str
    requisition_id: str | None = None
    location: GreenhouseLocation
    absolute_url: str
    language: str | None = None
    content: str | None = None
    application_deadline: str | None = None