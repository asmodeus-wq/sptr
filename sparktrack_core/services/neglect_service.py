from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Field, Path, Quest, Relationship, Resource
from sparktrack_core.services.workspace_service import WorkspaceScope, WorkspaceService


class NeglectService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.workspaces = WorkspaceService(session)

    def detect(self, scope: WorkspaceScope) -> dict[str, list[dict[str, object]]]:
        return {
            "quests": self._neglected_quests(scope),
            "fields": self._neglected_fields(scope),
            "resources": self._neglected_resources(scope),
            "artifacts": self._neglected_artifacts(scope),
        }

    def _neglected_quests(self, scope: WorkspaceScope) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for quest in self.session.scalars(select(Quest).where(Quest.status == "Active")):
            field = self.session.get(Field, quest.field_id)
            if field is None:
                continue
            path = self.session.get(Path, field.path_id)
            if path is None:
                continue
            if not self.workspaces.quest_belongs(field.id, path.id, scope):
                continue
            last = self._last_quest_activity(quest.id)
            days = self._days_since(last)
            if days >= 7:
                rows.append({
                    "id": quest.id,
                    "title": quest.title,
                    "path_name": path.name,
                    "field_name": field.name,
                    "days_since": days,
                    "status": "stalled" if days >= 21 else "neglected",
                })
        rows.sort(key=lambda row: row["days_since"], reverse=True)
        return rows[:12]

    def _neglected_fields(self, scope: WorkspaceScope) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for field in self.session.scalars(select(Field).where(Field.status == "Active")):
            path = self.session.get(Path, field.path_id)
            if path is None:
                continue
            if not self.workspaces.field_belongs(field.id, path.id, scope):
                continue
            last = self.session.scalar(
                select(func.max(Burst.created_at))
                .join(Quest, Burst.quest_id == Quest.id)
                .where(Quest.field_id == field.id)
            )
            days = self._days_since(last)
            if days >= 14:
                rows.append({
                    "id": field.id,
                    "title": field.name,
                    "path_name": path.name,
                    "days_since": days,
                    "status": "dormant",
                })
        rows.sort(key=lambda row: row["days_since"], reverse=True)
        return rows[:8]

    def _neglected_resources(self, scope: WorkspaceScope) -> list[dict[str, object]]:
        if scope.is_filtered:
            return []
        rows: list[dict[str, object]] = []
        for resource in self.session.scalars(select(Resource)):
            if resource.progress not in {"Not Started", "In Progress"}:
                continue
            days = self._days_since(resource.created_at)
            if days >= 14:
                rows.append({
                    "id": resource.id,
                    "title": resource.title,
                    "days_since": days,
                    "status": "untouched",
                })
        rows.sort(key=lambda row: row["days_since"], reverse=True)
        return rows[:8]

    def _neglected_artifacts(self, scope: WorkspaceScope) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for artifact in self.session.scalars(select(Artifact).order_by(Artifact.created_at)):
            linked = self.session.scalar(
                select(func.count(Relationship.id)).where(
                    Relationship.target_type == "artifact",
                    Relationship.target_id == artifact.id,
                )
            ) or 0
            days = self._days_since(artifact.created_at)
            if linked == 0 and days >= 7:
                rows.append({
                    "id": artifact.id,
                    "title": artifact.title,
                    "days_since": days,
                    "status": "unrevisited",
                })
        rows.sort(key=lambda row: row["days_since"], reverse=True)
        return rows[:8]

    def _last_quest_activity(self, quest_id: int) -> datetime | None:
        burst_last = self.session.scalar(
            select(func.max(Burst.created_at)).where(Burst.quest_id == quest_id)
        )
        artifact_last = self.session.scalar(
            select(func.max(Relationship.created_at)).where(
                Relationship.target_type == "quest",
                Relationship.target_id == quest_id,
            )
        )
        candidates = [value for value in (burst_last, artifact_last) if value is not None]
        return max(candidates) if candidates else None

    def _days_since(self, timestamp: datetime | None) -> int:
        if timestamp is None:
            return 999
        return max(0, (datetime.now() - timestamp).days)