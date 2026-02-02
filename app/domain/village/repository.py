from sqlalchemy.orm import Session

from app.domain.common.repository import BaseRepository
from app.domain.village.model import Village


class VillageRepository(BaseRepository[Village]):
    model = Village

    def __init__(self, db: Session) -> None:
        super().__init__(db)
