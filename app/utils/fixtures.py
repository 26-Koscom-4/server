import json
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"

@dataclass
class FixtureNotFound(Exception):
    filename: str

@dataclass
class FixtureInvalid(Exception):
    filename: str
    reason: str

def load_fixture(filename: str) -> Dict[str, Any]:
    path = FIXTURES_DIR / filename
    if not path.exists():
        raise FixtureNotFound(filename=filename)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise FixtureInvalid(filename=filename, reason=str(exc)) from exc
