from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.core.config import settings
from app.utils.fixtures import FixtureInvalid, FixtureNotFound

app = FastAPI(title=settings.PROJECT_NAME)

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
