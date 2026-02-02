from sqlalchemy.orm import Session

from app.domain.common.repository import BaseRepository
from app.domain.portfolio.model import UserPortfolio


class PortfolioRepository(BaseRepository[UserPortfolio]):
    model = UserPortfolio

    def __init__(self, db: Session) -> None:
        super().__init__(db)
