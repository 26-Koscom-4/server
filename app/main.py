from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.services.briefing.scheduled_briefing import run_scheduled_briefing
from app.utils.fixtures import FixtureInvalid, FixtureNotFound

_scheduler: Optional[BackgroundScheduler] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """앱 시작 시 DB 연결 확인 및 APScheduler 등록(매일 9시·17시), 종료 시 리소스 정리."""
    # Database connection check
    try:
        with engine.connect() as connection:
            print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        raise

    # Start APScheduler
    global _scheduler
    _scheduler = BackgroundScheduler(timezone=settings.BRIEFING_SCHEDULE_TIMEZONE)
    _scheduler.add_job(
        run_scheduled_briefing,
        "cron",
        hour=9,
        minute=0,
        id="briefing_morning",
    )
    _scheduler.add_job(
        run_scheduled_briefing,
        "cron",
        hour=17,
        minute=0,
        id="briefing_evening",
    )
    _scheduler.start()
    print("✓ APScheduler started")

    yield

    # Shutdown
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
    engine.dispose()
    print("✓ Resources cleaned up")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(FixtureNotFound)
def fixture_not_found_handler(_request, exc: FixtureNotFound) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "FIXTURE_NOT_FOUND",
                "message": f"Fixture not found: {exc.filename}",
            }
        },
    )

@app.exception_handler(FixtureInvalid)
def fixture_invalid_handler(_request, exc: FixtureInvalid) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "FIXTURE_INVALID",
                "message": f"Failed to parse fixture: {exc.filename}",
            }
        },
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
