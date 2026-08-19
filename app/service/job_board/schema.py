from pydantic import BaseModel, ConfigDict


class GreenhouseLocation(BaseModel):
    name: str


class GreenhouseJob(BaseModel):
    id: int
    internal_job_id: int | None = None
    company_name: str | None = None
    title: str
    updated_at: str
    requisition_id: str | None = None
    location: GreenhouseLocation
    absolute_url: str
    language: str | None = None
    content: str | None = None
    application_deadline: str | None = None
    visa_sponsorship: bool | None = None
    years: int | None = None