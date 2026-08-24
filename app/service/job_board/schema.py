from pydantic import BaseModel, ConfigDict, Field


# class GreenhouseLocation(BaseModel):
#     name: str


# class GreenhouseJob(BaseModel):
#     id: int
#     internal_job_id: int | None = None
#     company_name: str | None = None
#     title: str
#     updated_at: str
#     requisition_id: str | None = None
#     location: GreenhouseLocation
#     absolute_url: str
#     language: str | None = None
#     content: str | None = None
#     application_deadline: str | None = None
#     visa_sponsorship: bool | None = None
#     years: int | None = None
#     skills: list[str] | None = None

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, HttpUrl


class RemoteType(str, Enum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"
    UNKNOWN = "unknown"


class ExperienceLevel(str, Enum):
    INTERN = "intern"
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    UNKNOWN = "unknown"


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    FREELANCE = "freelance"
    UNKNOWN = "unknown"


class JobSource(str, Enum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    WORKDAY = "workday"
    SMARTRECRUITERS = "smartrecruiters"
    CAREER_PAGE = "career_page"
    OTHER = "other"


class SalaryPeriod(str, Enum):
    HOURLY = "hourly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    UNKNOWN = "unknown"


class JobLocation(BaseModel):
    raw: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    country_code: str | None = None
    remote_type: RemoteType = RemoteType.UNKNOWN


class Salary(BaseModel):
    min_amount: float | None = None
    max_amount: float | None = None
    currency: str | None = None
    period: SalaryPeriod = SalaryPeriod.UNKNOWN


class NormalizedJob(BaseModel):
    # Identity
    source: JobSource | None = None
    source_job_id: str | None = None
    internal_job_id: int | None = None
    requisition_id: str | None = None

    # Company
    company_name: str

    # Core job information
    title: str
    description: str | None = None
    department: str | None = None
    team: str | None = None
    job_family: str | None = None
    content: str | None = None

    # Job type / seniority
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    # experience_level: ExperienceLevel = ExperienceLevel.UNKNOWN
    experience_level: str | None = None

    min_years_experience: float | None = None
    max_years_experience: float | None = None

    # Location
    location: JobLocation | None = None

    # Skills

    skills: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    required_languages: list[str] = Field(default_factory=list)

    # Languages
    posting_language: str | None = None
    required_languages: list[str] = []

    # Immigration / international hiring
    visa_sponsorship: bool | None = None
    visa_sponsorship_details: str | None = None
    relocation_support: bool | None = None
    relocation_details: str | None = None

    # Compensation
    salary: Salary | None = None

    # Application
    application_url: HttpUrl | None = None
    source_url: HttpUrl | None = None
    application_deadline: datetime | None = None

    # Lifecycle
    published_at: datetime | None = None
    updated_at: datetime | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    closed_at: datetime | None = None

    is_active: bool = True

    # Extraction / AI metadata
    extraction_confidence: float | None = None
    extraction_version: str | None = None


class JobAIExtraction(BaseModel):
    application_deadline: str | None = None

    visa_sponsorship: bool | None = None
    visa_sponsorship_details: str | None = None

    relocation_support: bool | None = None

    min_years_experience: float | None = None
    max_years_experience: float | None = None

    experience_level: str | None = None

    skills: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)

    required_languages: list[str] = Field(default_factory=list)