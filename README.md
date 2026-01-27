# FastAPI Hackathon Server

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Project layout

- `app/main.py`: FastAPI app entry
- `app/api/v1/endpoints/`: REST endpoints
- `app/core/`: config and settings
- `app/db/`: database session (placeholder)
- `app/models/`, `app/schemas/`, `app/crud/`: domain layers
- `tests/`: test placeholders
