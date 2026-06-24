from sqlalchemy import select
from sqlalchemy.orm import Session

from sparktrack_core.models import Path


class SeedService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def seed_defaults(self) -> None:
        exists = self.session.scalar(select(Path.id).limit(1))
        if exists:
            return

        self.session.add_all(
            [
                Path(name="Builder", description="Systems, software, ventures.", icon="B"),
                Path(name="Warrior", description="Body, discipline, capability.", icon="W"),
                Path(name="Philosopher", description="Reflection, principles, meaning.", icon="P"),
                Path(name="Creator", description="Writing, art, stories, craft.", icon="C"),
                Path(name="Steward", description="Resources, home, land, responsibility.", icon="S"),
                Path(name="Householder", description="Family, relationships, daily life.", icon="H"),
            ]
        )
