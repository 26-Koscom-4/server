from sqlalchemy.orm import Session

from app.domain.common.repository import BaseRepository
from app.domain.prompt.model import Prompt


class PromptRepository(BaseRepository[Prompt]):
    model = Prompt

    def __init__(self, db: Session) -> None:
        super().__init__(db)
