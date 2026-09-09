import logging

import requests
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from app.core.settings import settings
from app.service.job_board.schema import JobSource, NormalizedJob
from app.service.llm_integration.llm_service import llm_service
from app.utils.job_fields import (
    detect_visa_sponsorship,
    extract_experience_years,
    is_software_role,
)

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


greenhouse_boards = [
    "Cloudbeds",
    "Ebury",
    "Parloa",
    "Affirm",
    "rtbhouse",
    "n26",
    "celonis",
    "ionos",
    "hellofresh",
    "coinbase",
    "algolia",
    "squarespace",
    "prisma",
    "nice",
    "atolls",
    "dremio",
    "remote",
    "Canonical",
    "AlphaSights",
    "Tripadvisor",
    "Samsara",
    "Contentful",
    "Salsify",
    "Squarespace",
    "Rithum",
    "Monzo",
    "Optiver",
    "Vercel",
    "proton",
    "yld",
    "apaleo",
    "isomorphiclabs",
    "canonical",
    "ninjatrader",
]

ROLE_KEYWORDS = {
    "software engineer",
    "backend engineer",
    "frontend engineer",
    "full stack engineer",
    "Software Engineer I",
    "Associate Software Engineer",
    "Graduate Software Engineer",
    "New Grad Software Engineer",
    "Python Engineer",
    "Java Engineer",
    "Early Career Software Engineer",
    "Software Developer",
    "Graduate Developer",
}

SENIORITY_EXCLUSIONS = {
    "senior",
    "staff",
    "principal",
    "lead",
    "director",
    "manager",
    "head",
    "vp",
}

skills = [
    "Python",
    "Java",
    "FastAPI",
    "springboot",
    "nodejs",
    "Reactjs",
    "Typescript",
    "Html",
    "css",
    "javascript",
    "PostgreSQL",
    "SQL",
    "LLM",
    "RAG",
    "Docker",
    "AWS",
    "REST APIs",
    "Distributed Systems",
]

fit_role = {
    "target_roles": ROLE_KEYWORDS,
    "experience_years": 1,
    "skills": skills,
    # "locations": [
    #     "Germany",
    #     "Netherlands",
    #     "France",
    #     "Poland",
    #     "Italy",
    #     "Ireland"
    # ],
    "languages": ["English"],
    "max_experience_years": 2,
    "visa_sponsorship": True,
    "relocation": True,
}

VISA_POSITIVE_PATTERNS = [
    "visa sponsorship",
    "sponsor your visa",
    "sponsorship available",
    "we are able to offer visa sponsorship",
    "visa support",
]

BASE_URL = settings.greenhouse_url
SUFFIX = "/jobs"


def classify_seniority(title: str) -> str:
    title = title.lower()

    if any(x in title for x in SENIORITY_EXCLUSIONS):
        return "high"

    if "senior" in title:
        return "senior"

    if any(
        x in title
        for x in {
            "junior",
            "associate",
            "graduate",
            "new grad",
            "entry level",
            "entry-level",
            "early career",
            "intern",
        }
    ):
        return "early"

    return "unknown"


def classify_job(job: NormalizedJob) -> str:

    if not is_software_role(job.title):
        return "irrelevant"

    seniority = classify_seniority(job.title)

    if seniority == "high":
        return "irrelevant"

    return "candidate"


def ingest_all_companies():
    for company in greenhouse_boards:
        jobs = get_jobs_by_company(company)
        return jobs


def search_job(visa_sponsorship: bool):
    import json

    with open("app/examples/greenhouse_jobs.json", encoding="utf-8") as file:
        data = json.load(file)

    return [s for s in data["jobs"] if s["visa_sponsorship"] == visa_sponsorship]


def get_list_company():
    logger.info(
        "Querying list of jobs",
        extra={
            "event": "List of jobs",
        },
    )
    return greenhouse_boards


def get_all_jobs():

    all_jobs = []

    for company in greenhouse_boards:
        data = get_jobs_by_company(company)

        if data is None:
            continue

        for job in data:
            classification = classify_job(job)

            if classification == "candidate":
                all_jobs.append(job)

    return enrich_and_filter_jobs(all_jobs)


def get_jobs_by_company(company: str):
    url = f"{BASE_URL}/{company}{SUFFIX}"

    with tracer.start_as_current_span("greenhouse.fetch_jobs") as span:
        span.set_attribute(
            "job.source",
            "greenhouse",
        )
        span.set_attribute(
            "job.company",
            company,
        )

        try:
            http_response = requests.get(
                url,
                params={"content": "true"},
                timeout=30,
            )

            span.set_attribute(
                "http.response.status_code",
                http_response.status_code,
            )

            if http_response.status_code == 404:
                span.set_attribute(
                    "greenhouse.board_found",
                    False,
                )

                span.set_status(
                    Status(
                        StatusCode.ERROR,
                        "Greenhouse board not found",
                    )
                )

                return None

            http_response.raise_for_status()

            data = http_response.json()

            if "meta" not in data:
                span.set_status(
                    Status(
                        StatusCode.ERROR,
                        "Missing meta field",
                    )
                )

                span.add_event("greenhouse.invalid_response")

                return None

            jobs = data["jobs"]

            span.set_attribute(
                "jobs.fetched_count",
                len(jobs),
            )

            response = []

            for job in jobs:
                greenhouse_job = NormalizedJob.model_validate(job)

                greenhouse_job.source = JobSource.GREENHOUSE

                greenhouse_job.company_name = company

                greenhouse_job.visa_sponsorship = detect_visa_sponsorship(
                    job["content"]
                )

                greenhouse_job.min_years_experience = extract_experience_years(
                    job["content"]
                )

                classification = classify_job(greenhouse_job)

                if classification == "candidate":
                    response.append(greenhouse_job)

            span.set_attribute(
                "jobs.candidate_count",
                len(response),
            )

            span.set_status(Status(StatusCode.OK))

            return enrich_and_filter_jobs(response)

        except requests.exceptions.RequestException as exc:
            span.record_exception(exc)

            span.set_status(
                Status(
                    StatusCode.ERROR,
                    str(exc),
                )
            )

            raise


def enrich_job(job: NormalizedJob) -> NormalizedJob:
    extraction = llm_service.extract_fields(job)

    if extraction is None:
        return job

    extracted = extraction.model_dump(exclude_none=True)

    for field, value in extracted.items():
        setattr(job, field, value)

    return job


def soft_filter(job: NormalizedJob) -> NormalizedJob | None:
    data = enrich_job(job)
    if data.min_years_experience is not None:
        if data.min_years_experience >= 6:
            return None

    if data.experience_level:
        level = data.experience_level.lower()

        if level in {"staff", "principal", "director"}:
            return None

    return data


def enrich_and_filter_jobs(
    jobs: list[NormalizedJob],
) -> list[NormalizedJob]:
    with tracer.start_as_current_span("enrich_and_filter_jobs") as span:
        span.set_attribute(
            "jobs.input_count",
            len(jobs),
        )

        result = []

        for job in jobs:
            data = soft_filter(job)

            if data is None:
                continue

            result.append(data)

        span.set_attribute(
            "jobs.output_count",
            len(result),
        )

        return result
