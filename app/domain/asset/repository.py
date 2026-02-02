from sqlalchemy.orm import Session

from app.domain.asset.model import Asset
from app.domain.common.repository import BaseRepository


class AssetRepository(BaseRepository[Asset]):
    model = Asset

    def __init__(self, db: Session) -> None:
        super().__init__(db)
