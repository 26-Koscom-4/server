from typing import Any, Dict, Optional

from fastapi import APIRouter, status

from app.schemas.auth.request import LoginRequest
from app.schemas.auth.response import LoginResponse
from app.schemas.briefing.response import BriefingResponse
from app.schemas.common.error import ErrorResponse
from app.schemas.common.response import OkResponse
from app.schemas.daily.response import DailyResponse
from app.schemas.investment_test.request import InvestmentTestResultRequest
from app.schemas.investment_test.response import InvestmentTestResponse
from app.schemas.main.response import MainResponse
from app.schemas.mydata.request import MydataCompleteRequest
from app.schemas.mydata.response import MydataResponse
from app.schemas.mypage.response import MypageResponse
from app.schemas.neighbors.response import NeighborsResponse
from app.schemas.villages.request import CreateVillageRequest
from app.schemas.villages.response import (
    CreateVillageResponse,
    VillageModalResponse,
    VillagesResponse,
)
from app.utils.fixtures import load_fixture

router = APIRouter()

_state: Dict[str, Optional[Dict[str, Any]]] = {
    "investment_test": None,
    "mydata_integration": None,
}

FIXTURE_ERROR_RESPONSES = {
    404: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
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


@router.get("/main", response_model=MainResponse, responses=FIXTURE_ERROR_RESPONSES)
def get_main() -> MainResponse:
    data = load_fixture("ui_state_main.json")
    return MainResponse.model_validate(data)


@router.get("/villages", response_model=VillagesResponse, responses=FIXTURE_ERROR_RESPONSES)
def get_villages() -> VillagesResponse:
    data = load_fixture("ui_state_villages.json")
    return VillagesResponse.model_validate(data)


@router.get("/briefing", response_model=BriefingResponse, responses=FIXTURE_ERROR_RESPONSES)
def get_briefing() -> BriefingResponse:
    data = load_fixture("ui_state_briefing.json")
    return BriefingResponse.model_validate(data)


@router.get("/daily", response_model=DailyResponse, responses=FIXTURE_ERROR_RESPONSES)
def get_daily() -> DailyResponse:
    data = load_fixture("ui_state_daily.json")
    return DailyResponse.model_validate(data)


@router.get("/neighbors", response_model=NeighborsResponse, responses=FIXTURE_ERROR_RESPONSES)
def get_neighbors() -> NeighborsResponse:
    data = load_fixture("ui_state_neighbors.json")
    return NeighborsResponse.model_validate(data)


@router.get("/mypage", response_model=MypageResponse, responses=FIXTURE_ERROR_RESPONSES)
def get_mypage() -> MypageResponse:
    mypage = load_fixture("ui_state_mypage.json")
    updated = _apply_mypage_overrides(mypage)
    return MypageResponse.model_validate(updated)


@router.get(
    "/villages/{village_id}",
    response_model=VillageModalResponse,
    responses=FIXTURE_ERROR_RESPONSES,
)
def get_village_modal(village_id: str) -> VillageModalResponse:
    _ = village_id
    data = load_fixture("ui_state_villageModal.json")
    return VillageModalResponse.model_validate(data)


@router.get(
    "/investment-test",
    response_model=InvestmentTestResponse,
    responses=FIXTURE_ERROR_RESPONSES,
)
def get_investment_test() -> InvestmentTestResponse:
    data = load_fixture("ui_state_investmentTest.json")
    return InvestmentTestResponse.model_validate(data)


@router.get("/mydata", response_model=MydataResponse, responses=FIXTURE_ERROR_RESPONSES)
def get_mydata() -> MydataResponse:
    data = load_fixture("ui_state_mydata.json")
    return MydataResponse.model_validate(data)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    _ = payload
    return LoginResponse(accessToken="mock-token", user={"name": "김직장"})


@router.post("/logout", response_model=OkResponse)
def logout() -> OkResponse:
    return OkResponse(ok=True)


@router.post(
    "/villages",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateVillageResponse,
)
def create_village(payload: CreateVillageRequest) -> CreateVillageResponse:
    return CreateVillageResponse(
        status="created",
        payload=payload.model_dump(exclude_none=True),
    )


@router.post("/investment-test/result", response_model=OkResponse)
def save_investment_result(payload: InvestmentTestResultRequest) -> OkResponse:
    _state["investment_test"] = payload.model_dump(exclude_none=True)
    return OkResponse(ok=True)


@router.post("/mydata/complete", response_model=OkResponse)
def complete_mydata(payload: MydataCompleteRequest) -> OkResponse:
    _state["mydata_integration"] = payload.model_dump(exclude_none=True)
    return OkResponse(ok=True)
