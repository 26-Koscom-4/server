from fastapi import APIRouter

from app.domain.asset import controller as asset
from app.domain.briefing import controller as briefing
from app.domain.portfolio import controller as portfolio
from app.domain.prompt import controller as prompt
from app.domain.user import controller as user
from app.domain.village import controller as village

api_router = APIRouter()

api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(asset.router, prefix="/assets", tags=["assets"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(village.router, prefix="/villages", tags=["villages"])
api_router.include_router(prompt.router, prefix="/prompts", tags=["prompts"])
api_router.include_router(briefing.router, prefix="/briefing", tags=["briefing"])
