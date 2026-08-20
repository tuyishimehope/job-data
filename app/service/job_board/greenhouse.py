import re
import requests

from app.service.job_board.schema import GreenhouseJob


greenhouse_boards = [
    "Scopely",
    "Cloudbeds",
    # "Ebury",
    # "Parloa",
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

BASE_URL = "https://boards-api.greenhouse.io/v1/boards"
SUFFIX = "/jobs"


def ingest_all_companies():
    for company in greenhouse_boards:
        jobs = get_jobs_by_company(company)

        # for job in jobs:
        # save_job(job)
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


def extract_experience_years(text: str) -> int | None:
    text = text.lower()

    patterns = [
        r"(\d+)\+?\s*(?:years|yrs)\s+of\s+experience",
        r"(\d+)\+?\s*(?:years|yrs)\s+experience",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return int(match.group(1))

    return None


def detect_visa_sponsorship(text: str) -> bool | None:
    text = text.lower()

    negative_patterns = [
        "no visa sponsorship",
        "without visa sponsorship",
        "unable to sponsor",
        "cannot sponsor",
        "do not sponsor",
        "does not sponsor",
        "not eligible for sponsorship",
        "will not sponsor",
    ]

    for pattern in negative_patterns:
        if pattern in text:
            return False

    positive_patterns = [
        "visa sponsorship available",
        "visa sponsorship is available",
        "we offer visa sponsorship",
        "we provide visa sponsorship",
        "visa sponsorship provided",
        "we are able to offer visa sponsorship",
        "sponsor your visa",
    ]

    for pattern in positive_patterns:
        if pattern in text:
            return True

    return None


def get_list_company():
    return greenhouse_boards


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


def is_software_role(title: str) -> bool:
    title = title.lower()

    return any(
        keyword in title
        for keyword in ROLE_KEYWORDS
    )


def classify_job(job: GreenhouseJob) -> str:

    if not is_software_role(job.title):
        return "irrelevant"

    seniority = classify_seniority(job.title)

    if seniority == "high":
        return "irrelevant"

    return "candidate"


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

    return all_jobs


def get_jobs_by_company(company: str):

    url = f"{BASE_URL}/{company}{SUFFIX}"

    http_response = requests.get(
        url,
        params={"content": "true"},
        timeout=30,
    )

    if http_response.status_code == 404:
        print(f"{company}: board not found")
        return None

    data = http_response.json()

    if 'meta' not in data:
        return None
    else:
        print(f"{company}: {data['meta']['total']} jobs")
        response = []

        for job in data["jobs"]:
            greenhouse_job = GreenhouseJob.model_validate(job)
            greenhouse_job.company_name = company
            greenhouse_job.visa_sponsorship = detect_visa_sponsorship(
                job['content'])
            greenhouse_job.years = extract_experience_years(job['content'])
            response.append(greenhouse_job)

        return response
