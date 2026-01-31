from fastapi import APIRouter
from app.api.v1.endpoints import mock

api_router = APIRouter()

api_router.include_router(mock.router, tags=["mock"])
