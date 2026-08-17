import requests

from app.service.job_board.schema import GreenhouseJob


greenhouse_boards = [
    "Anthropic",
    # "Scopely",
    # "Cloudbeds",
    # "Ebury",
    # "Parloa",
    # "DoiT",
    # "HSO International",
    # "Getnet Platforms",
    # "Santander",
    # "Affirm",
    # "rtbhouse",
    # "n26",
    # "celonis",
    # "ionos",
    # "hellofresh",
    # "coinbase",
    # "planet",
    # "algolia",
    # "squarespace",
    # "prisma",
    # "nice",
    # "atolls",
    # "dremio",
    # "remote",
    # "armis",
]

KEYWORDS = {
    "software engineer",
    "software developer",
    "backend engineer",
    "backend developer",
    "frontend engineer",
    "frontend developer",
    "full stack engineer",
    "full-stack engineer",
}


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


BASE_URL = "https://boards-api.greenhouse.io/v1/boards"
SUFFIX = "/jobs"


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

    http_response.raise_for_status()

    data = http_response.json()

    print(f"{company}: {data['meta']['total']} jobs")

    for job in data["jobs"][:5]:
        print("=" * 80)
        print("ID:", job["id"])
        print("Company_name:", job["company_name"])
        print("Title:", job["title"])
        print("Location:", job["location"]["name"])
        print("URL:", job["absolute_url"])
        print("Language:", job["language"])
        print("Content:", job["content"])
        print("Updated_at:", job["updated_at"])
        print("first_published:", job["first_published"])
        print("application_deadline:", job["application_deadline"])

    response = []

    for job in data["jobs"]:
        greenhouse_job = GreenhouseJob.model_validate(job)
        response.append(greenhouse_job)

    return response
