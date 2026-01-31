from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, status

from app.utils.fixtures import load_fixture

router = APIRouter()

_state: Dict[str, Optional[Dict[str, Any]]] = {
    "investment_test": None,
    "mydata_integration": None,
}

def _apply_mypage_overrides(mypage: Dict[str, Any]) -> Dict[str, Any]:
    investment_override = _state.get("investment_test")
    if investment_override:
        investment = mypage.get("investment_test", {})
        investment.update(investment_override)
        mypage["investment_test"] = investment

    mydata_override = _state.get("mydata_integration")
    if mydata_override:
        mydata = mypage.get("mydata_integration", {})
        mydata.update(mydata_override)
        mypage["mydata_integration"] = mydata

    return mypage

@router.get("/main")
def get_main() -> Dict[str, Any]:
    return load_fixture("ui_state_main.json")

@router.get("/villages")
def get_villages() -> Dict[str, Any]:
    return load_fixture("ui_state_villages.json")

@router.get("/briefing")
def get_briefing() -> Dict[str, Any]:
    return load_fixture("ui_state_briefing.json")

@router.get("/daily")
def get_daily() -> Dict[str, Any]:
    return load_fixture("ui_state_daily.json")

@router.get("/neighbors")
def get_neighbors() -> Dict[str, Any]:
    return load_fixture("ui_state_neighbors.json")

@router.get("/mypage")
def get_mypage() -> Dict[str, Any]:
    mypage = load_fixture("ui_state_mypage.json")
    return _apply_mypage_overrides(mypage)

@router.get("/villages/{village_id}")
def get_village_modal(village_id: str) -> Dict[str, Any]:
    _ = village_id
    return load_fixture("ui_state_villageModal.json")

@router.get("/investment-test")
def get_investment_test() -> Dict[str, Any]:
    return load_fixture("ui_state_investmentTest.json")

@router.get("/mydata")
def get_mydata() -> Dict[str, Any]:
    return load_fixture("ui_state_mydata.json")

@router.post("/login")
def login(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    _ = payload
    return {"accessToken": "mock-token", "user": {"name": "김직장"}}

@router.post("/logout")
def logout() -> Dict[str, Any]:
    return {"ok": True}

@router.post("/villages", status_code=status.HTTP_201_CREATED)
def create_village(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    return {"status": "created", "payload": payload}

@router.post("/investment-test/result")
def save_investment_result(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    _state["investment_test"] = payload
    return {"ok": True}

@router.post("/mydata/complete")
def complete_mydata(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    _state["mydata_integration"] = payload
    return {"ok": True}
