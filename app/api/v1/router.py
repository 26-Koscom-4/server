from fastapi import APIRouter

from app.api.v1.endpoints import briefing, mock

api_router = APIRouter()

api_router.include_router(mock.router, tags=["mock"])
api_router.include_router(briefing.router, prefix="/briefing", tags=["briefing"])
