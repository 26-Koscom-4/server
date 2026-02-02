from sqlalchemy.orm import Session

from app.domain.common.repository import BaseRepository
from app.domain.user.model import User


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, db: Session) -> None:
        super().__init__(db)
