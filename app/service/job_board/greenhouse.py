import requests

from app.service.job_board.schema import GreenhouseJob


greenhouse_boards = [
    # "Anthropic",
    "Scopely",
    # "Cloudbeds",
    # "Ebury",
    # "Parloa",
    # "Affirm",
    # "rtbhouse",
    # "n26",
    # "celonis",
    # "ionos",
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
]

KEYWORDS = {
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

BASE_URL = "https://boards-api.greenhouse.io/v1/boards"
SUFFIX = "/jobs"


def check_company_board(company: str):
    try:
        response = requests.get(f"{BASE_URL}/company/{SUFFIX}")
        if response.status_code == 404:
            print(f"{company}: board not found")
            return False
        
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        print("An error occured")
        return False


def is_relevant_job(job: GreenhouseJob) -> bool:
    title = job.title.lower()

    return any(keyword in title for keyword in KEYWORDS)


def get_list_company():
    return greenhouse_boards


def get_all_jobs():

    all_jobs = []

    for company in greenhouse_boards:

        data = get_jobs_by_company(company)

        if data is None:
            continue

        relevant_jobs = [
            job
            for job in data
            if is_relevant_job(job)
        ]

        all_jobs.extend(relevant_jobs)

    return all_jobs


def get_jobs_by_company(company: str):

    url = f"{BASE_URL}/{company}{SUFFIX}"

    http_response = requests.get(
        url,
        params={"content": "true"},
        timeout=30,
    )

    result = check_company_board(company)
    if result is False:
        return None

    data = http_response.json()

    if 'meta' not in data:
        return None
    else:
        print(f"{company}: {data['meta']['total']} jobs")

        response = []

        for job in data["jobs"]:
            greenhouse_job = GreenhouseJob.model_validate(job)
            response.append(greenhouse_job)

        return response
