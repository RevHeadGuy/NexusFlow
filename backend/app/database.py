import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, echo=settings.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create tables automatically for local SQLite only.

    For any other engine (e.g. PostgreSQL in a shared/managed deployment),
    Alembic migrations are the source of truth — run ``alembic upgrade head``
    instead of relying on startup table creation. Auto-creating on a managed
    database would bypass migration history and risk schema drift.
    """
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    else:
        logger.info(
            "Skipping automatic table creation for non-SQLite database; "
            "apply schema with `alembic upgrade head`."
        )
