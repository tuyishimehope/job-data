import logging
from uuid import uuid4
import requests
import newrelic.agent

from app.core.tracing import Span
from app.service.job_board.schema import NormalizedJob, JobSource
from app.core.settings import settings
from app.utils.job_fields import extract_experience_years, detect_visa_sponsorship, is_software_role
from app.service.llm_integration.llm_service import llm_service

logger = logging.getLogger(__name__)


greenhouse_boards = [
    "Cloudbeds",
    "Ebury",
    "Parloa",
    # "Affirm",
    # "rtbhouse",
    # "n26",
    # "celonis",
    # "ionos",
    #
    # "hellofresh",
    # "coinbase",
    # "algolia",
    # "squarespace",
    # "prisma",
    # "nice",
    # "atolls",
    # "dremio",
    # "remote",
    # "Canonical",
    #
    # "AlphaSights",
    # "Tripadvisor",
    # "Samsara",
    # "Contentful",
    # "Salsify",
    # "Squarespace",
    # "Rithum",
    # "Monzo",
    # "Optiver",
    # "Vercel",
    # "proton",
    # "yld",
    # "apaleo",
    # "isomorphiclabs",
    # "canonical",
    # "ninjatrader",
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
    "Graduate Developer"
}

SENIORITY_EXCLUSIONS = {
    "senior",
    "staff",
    "principal",
    "lead",
    "director",
    "manager",
    "head",
    "vp"
}

skills = ["Python",
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
          "Distributed Systems"]

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
    "languages": [
        "English"
    ],
    "max_experience_years": 2,
    "visa_sponsorship": True,
    "relocation": True
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

    if any(x in title for x in {
        "junior",
        "associate",
        "graduate",
        "new grad",
        "entry level",
        "entry-level",
        "early career",
        "intern",
    }):
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
        return None


def search_job(visa_sponsorship: bool):
    import json

    with open("app/examples/greenhouse_jobs.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    return [
        s
        for s in data["jobs"]
        if s["visa_sponsorship"] == visa_sponsorship
    ]


def get_list_company():
    logger.info("Querying list of jobs", extra={
        "event": "List of jobs",
    })
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

    # result = []
    # for job in all_jobs:
    #     job = soft_filter(job)
    #     if job is None:
    #         continue
    #     result.append(job)
    # return result
    return enrich_and_filter_jobs(all_jobs)


def get_jobs_by_company(company: str):
    # trace_id = str(uuid4())
    # root_span = Span(
    #     name="GET /companies/"+company,
    #     trace_id=trace_id,
    # )
    logger.info(
        "Starting Greenhouse ingestion company",
        extra={
            "company": company,
            "event": "list_jobs_requested",
            "company": company},
    )

    url = f"{BASE_URL}/{company}{SUFFIX}"
    try:

        # child_span = Span(
        #     name="fetch_greenhouse_jobs",
        #     trace_id=trace_id,
        #     parent_span_id=root_span.span_id,
        # )
        http_response = requests.get(
            url,
            params={"content": "true"},
            timeout=30,
        )

        if http_response.status_code == 404:
            logger.warning(
                "Greenhouse board not found company=%s",
                company,
            )
            return None

        http_response.raise_for_status()
        data = http_response.json()

        if "meta" not in data:
            logger.warning(
                "Unexpected Greenhouse response",
                extra={
                    "event": "greenhouse_invalid_response",
                    "company": company,
                    "missing_field": "meta",
                },
            )
            return None
        else:
            logger.info(
                "Greenhouse jobs fetched",
                extra={
                    "event": "greenhouse_jobs_fetched",
                    "company": company,
                    "total": data["meta"]["total"],
                },
            )
            response = []

            for job in data["jobs"]:
                greenhouse_job = NormalizedJob.model_validate(job)
                greenhouse_job.source = JobSource.GREENHOUSE
                greenhouse_job.company_name = company
                greenhouse_job.visa_sponsorship = detect_visa_sponsorship(
                    job['content'])
                greenhouse_job.min_years_experience = extract_experience_years(
                    job['content'])

                classification = classify_job(greenhouse_job)

                if classification == "candidate":
                    response.append(greenhouse_job)

            # result = []

            # for job in response:
            #     data = soft_filter(job=job)
            #     if data is None:
            #         continue
            #     result.append(data)

            # return result
            return enrich_and_filter_jobs(response)
    except requests.exceptions.RequestException:
        logger.exception(
            "Greenhouse request failed",
            extra={
                "event": "greenhouse_request_failed",
                "company": company,
            },
        )
        return None
    finally:
        pass
        # root_span.finish()
        # child_span.finish()


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


@newrelic.agent.function_trace(
    name="enrich_and_filter_jobs"
)
def enrich_and_filter_jobs(
    jobs: list[NormalizedJob],
) -> list[NormalizedJob]:

    result = []

    for job in jobs:
        data = soft_filter(job)

        if data is None:
            continue

        result.append(data)

    return result
