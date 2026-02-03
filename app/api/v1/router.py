from fastapi import APIRouter

from app.domain.dashboard import controller as dashboard

api_router = APIRouter()

api_router.include_router(dashboard.router, tags=["dashboard"])
