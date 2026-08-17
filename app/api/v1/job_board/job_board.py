from fastapi import APIRouter

from app.service.job_board.greenhouse import get_all_jobs, get_jobs_by_company, get_list_company

router = APIRouter(prefix="/api/v1/job-board", tags=["/job-board"])


@router.get("/company")
def get_list_company_endpoint():
    return get_list_company()

@router.get("/company/?company_name")
def get_jobs_company_name_endpoint(company_name: str):
    return get_jobs_by_company(company=company_name)

@router.get("/")
def get_jobs_endpoint():
    jobs = get_all_jobs()

    return {
        "total": len(jobs),
        "jobs": jobs,
    }