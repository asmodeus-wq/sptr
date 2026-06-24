from sqlalchemy.orm import Session

from sparktrack_core.models import (
    Artifact,
    Burst,
    Field,
    Path,
    Principle,
    Quest,
    Relationship,
    Resource,
    Season,
)
from sparktrack_core.repositories.base import Repository


class PathRepository(Repository[Path]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Path)


class FieldRepository(Repository[Field]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Field)


class QuestRepository(Repository[Quest]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Quest)


class BurstRepository(Repository[Burst]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Burst)


class ArtifactRepository(Repository[Artifact]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Artifact)


class ResourceRepository(Repository[Resource]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Resource)


class SeasonRepository(Repository[Season]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Season)


class PrincipleRepository(Repository[Principle]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Principle)


class RelationshipRepository(Repository[Relationship]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Relationship)
