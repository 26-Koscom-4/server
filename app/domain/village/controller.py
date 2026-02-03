from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.village.model import Village, VillageAsset
from app.domain.village.schema.request import VillageCreateRequest
from app.domain.village.schema.response import VillageCreateResponse

router = APIRouter()


@router.post("", response_model=VillageCreateResponse)
def create_village(
    payload: VillageCreateRequest,
    db: Session = Depends(get_db),
) -> VillageCreateResponse:
    village = Village(
        user_id=payload.user_id,
        name=payload.name,
        icon=payload.icon,
        type=payload.type,
        goal=payload.goal,
        village_type="CUSTOM",
        village_profile=". ".join(payload.strategy_items).strip() if payload.strategy_items else None,
    )
    db.add(village)
    db.flush()

    if not payload.assets:
        raise HTTPException(status_code=400, detail="assets must not be empty.")
    for a in payload.assets:
        db.add(VillageAsset(village_id=village.village_id, asset_id=a.asset_id))
    db.commit()
    return VillageCreateResponse(village_id=village.village_id)
