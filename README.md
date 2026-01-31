# FastAPI Hackathon Server

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run

```powershell
uvicorn app.main:app --reload
```

## Endpoints

- GET /health
- GET /api/main
- GET /api/villages
- GET /api/briefing
- GET /api/daily
- GET /api/neighbors
- GET /api/mypage
- GET /api/villages/{id}
- GET /api/investment-test
- GET /api/mydata
- POST /api/login
- POST /api/logout
- POST /api/villages
- POST /api/investment-test/result
- POST /api/mydata/complete

## Project layout

- `app/main.py`: FastAPI app entry
- `app/api/v1/endpoints/`: REST endpoints
- `app/core/`: config and settings
- `app/db/`: database session (placeholder)
- `app/models/`, `app/schemas/`, `app/crud/`: domain layers
- `tests/`: test placeholders
