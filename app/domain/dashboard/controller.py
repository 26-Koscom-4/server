from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.dashboard.schema.response import DashboardResponse
from app.domain.dashboard.service import get_dashboard

router = APIRouter()


@router.get("/dashboard/{userId}", response_model=DashboardResponse)
def read_dashboard(userId: int, db: Session = Depends(get_db)) -> DashboardResponse:
    dashboard = get_dashboard(userId, db)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dashboard
