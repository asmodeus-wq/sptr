import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sparktrack_core.database.base import Base
from sparktrack_core.database.migrations import run_migrations
from sparktrack_core.models import entities  # noqa: F401 - registers ORM models


def default_database_path() -> Path:
    configured = os.getenv("SPARKTRACK_DB_PATH")
    if configured:
        return Path(configured).expanduser()

    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "SparkTrack" / "sparktrack.db"

    return Path.home() / ".sparktrack" / "sparktrack.db"


class Database:
    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or default_database_path()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{self.database_path}", future=True)
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
            future=True,
        )

    def initialize(self) -> None:
        Base.metadata.create_all(self.engine)
        run_migrations(self.engine)

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
