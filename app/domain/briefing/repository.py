from sqlalchemy.orm import Session

from app.domain.common.repository import BaseRepository


class BriefingRepository(BaseRepository[object]):
    model = None

    def __init__(self, db: Session) -> None:
        super().__init__(db)
