from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.dashboard import (
    DashboardEvaluationsResponse,
    DashboardJobsResponse,
    DashboardOverviewResponse,
    DashboardRetrievalResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    db: Session = Depends(get_db),
) -> DashboardOverviewResponse:
    service = DashboardService(db)
    return service.get_overview()


@router.get("/evaluations", response_model=DashboardEvaluationsResponse)
def get_dashboard_evaluations(
    db: Session = Depends(get_db),
) -> DashboardEvaluationsResponse:
    service = DashboardService(db)
    return service.get_evaluations()


@router.get("/retrieval", response_model=DashboardRetrievalResponse)
def get_dashboard_retrieval(
    db: Session = Depends(get_db),
) -> DashboardRetrievalResponse:
    service = DashboardService(db)
    return service.get_retrieval()


@router.get("/jobs", response_model=DashboardJobsResponse)
def get_dashboard_jobs(
    db: Session = Depends(get_db),
) -> DashboardJobsResponse:
    service = DashboardService(db)
    return service.get_jobs()
