from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool

from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Maximum overflow connections
    echo=False,          # Set to True for SQL query logging
)


# Set MySQL session variables for timezone handling
@event.listens_for(Pool, "connect")
def set_mysql_pragma(dbapi_conn, connection_record):
    """Set MySQL session timezone to UTC"""
    cursor = dbapi_conn.cursor()
    cursor.execute("SET time_zone = '+00:00'")
    cursor.close()


# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for getting database sessions.

    Usage in FastAPI:
        @app.get("/users/")
        def read_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.
    This will create all tables defined in the models.
    """
    from app.domain.common.model import Base
    import app.models  # ensure models are registered
    Base.metadata.create_all(bind=engine)
