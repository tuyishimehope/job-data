from fastapi import APIRouter

from app.service.job_board.greenhouse import get_all_jobs, get_jobs_by_company, get_list_company, search_job

router = APIRouter(prefix="/api/v1/job-board", tags=["/job-board"])


@router.get("/companies")
def get_list_company_endpoint():
    names = get_list_company()
    return {"total": len(names), "names": names}


@router.get("/companies/{company_name}")
def get_jobs_company_name_endpoint(company_name: str):
    jobs = get_jobs_by_company(company=company_name)
    if jobs is None:
        return None
    return {
        "total": len(jobs),
        "jobs": jobs,
    }


@router.get("/")
def get_jobs_endpoint():
    jobs = get_all_jobs()

    return {
        "total": len(jobs),
        "jobs": jobs,
    }
    
@router.get("/ingest")
def ingest_all_companies_endpoint():
    return {"status": "Pending"}
    
@router.get("/jobs/search")
def search(visa_sponsorship: bool):
    return search_job(visa_sponsorship=visa_sponsorship)



# GET /api/v1/job-board/jobs/{id}

# GET /api/v1/job-board/jobs/matches