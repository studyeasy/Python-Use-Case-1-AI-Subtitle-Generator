from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def _ensure_sqlite_dir(url: str) -> None:
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return
    db_path = Path(url.replace("sqlite:///", "", 1))
    db_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(settings.database_url)

connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass
