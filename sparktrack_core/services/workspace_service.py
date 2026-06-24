from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from sparktrack_core.models import Field, Path


@dataclass(frozen=True)
class WorkspaceScope:
    id: str
    name: str
    path_id: int | None = None
    field_id: int | None = None

    @property
    def is_filtered(self) -> bool:
        return self.path_id is not None or self.field_id is not None


@dataclass(frozen=True)
class WorkspaceProfile:
    scope: WorkspaceScope
    description: str
    primary_abstraction: str = "workspace"

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.scope.id,
            "name": self.scope.name,
            "path_id": self.scope.path_id,
            "field_id": self.scope.field_id,
            "description": self.description,
            "primary_abstraction": self.primary_abstraction,
        }


class WorkspaceService:
    """Workspaces are filter presets — not database entities."""

    ALL = WorkspaceScope(id="all", name="All Workspaces")

    def __init__(self, session: Session) -> None:
        self.session = session

    CURATED_PATH_NAMES = {
        "Builder", "Philosopher", "Warrior", "Creator",
        "Householder", "Steward",
    }

    def list_workspaces(self) -> list[WorkspaceScope]:
        """Primary workspaces: path-level dimensions + notable fields."""
        workspaces: list[WorkspaceScope] = []
        paths = list(self.session.scalars(select(Path).order_by(Path.name)))
        for path in paths:
            workspaces.append(
                WorkspaceScope(id=f"path:{path.id}", name=path.name, path_id=path.id)
            )

        notable_fields = {"SparkTrack", "AI Systems", "Writing", "Osho", "Muay Thai"}
        fields = self.session.scalars(
            select(Field).join(Path).order_by(Path.name, Field.name)
        )
        for field in fields:
            if field.name in notable_fields:
                workspaces.append(
                    WorkspaceScope(
                        id=f"field:{field.id}",
                        name=field.name,
                        path_id=field.path_id,
                        field_id=field.id,
                    )
                )
        return workspaces

    def list_all_scopes(self) -> list[WorkspaceScope]:
        """Includes 'All' scope for internal filtering."""
        return [self.ALL, *self.list_workspaces()]

    def get_workspace(self, workspace_id: str) -> WorkspaceScope:
        if workspace_id in ("all", ""):
            return self.ALL
        for workspace in self.list_all_scopes():
            if workspace.id == workspace_id:
                return workspace
        return self.ALL

    def profile(self, workspace_id: str) -> WorkspaceProfile:
        scope = self.get_workspace(workspace_id)
        if scope.field_id is not None:
            description = "Focused operating environment for a field of practice."
        elif scope.path_id is not None:
            description = "Life-dimension operating environment."
        else:
            description = "Global operating environment across all workspaces."
        return WorkspaceProfile(scope=scope, description=description)

    def quest_belongs(self, quest_field_id: int, quest_path_id: int, scope: WorkspaceScope) -> bool:
        if not scope.is_filtered:
            return True
        if scope.field_id is not None:
            return quest_field_id == scope.field_id
        if scope.path_id is not None:
            return quest_path_id == scope.path_id
        return True

    def field_belongs(self, field_id: int, path_id: int, scope: WorkspaceScope) -> bool:
        if not scope.is_filtered:
            return True
        if scope.field_id is not None:
            return field_id == scope.field_id
        if scope.path_id is not None:
            return path_id == scope.path_id
        return True
