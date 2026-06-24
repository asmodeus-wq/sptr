from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Field, Path, Quest, Relationship
from sparktrack_core.services.workspace_service import WorkspaceScope, WorkspaceService

MAX_BAR = 10


class MomentumService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.workspaces = WorkspaceService(session)
        self.cutoff = datetime.now() - timedelta(days=14)

    def quest_momentum(self, scope: WorkspaceScope) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        quests = self.session.scalars(select(Quest).where(Quest.status == "Active"))
        for quest in quests:
            field = self.session.get(Field, quest.field_id)
            if field is None:
                continue
            path = self.session.get(Path, field.path_id)
            if path is None:
                continue
            if not self.workspaces.quest_belongs(field.id, path.id, scope):
                continue
            score = self._quest_score(quest.id)
            rows.append({
                "id": quest.id,
                "title": quest.title,
                "field_name": field.name,
                "path_name": path.name,
                "score": score,
                "bar": self._bar(score),
                "status_label": self._status_label(score),
            })
        rows.sort(key=lambda row: row["score"], reverse=True)
        return rows

    def field_momentum(self, scope: WorkspaceScope) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        fields = self.session.scalars(select(Field).where(Field.status == "Active"))
        for field in fields:
            path = self.session.get(Path, field.path_id)
            if path is None:
                continue
            if not self.workspaces.field_belongs(field.id, path.id, scope):
                continue
            score = self._field_score(field.id)
            rows.append({
                "id": field.id,
                "title": field.name,
                "path_name": path.name,
                "score": score,
                "bar": self._bar(score),
                "status_label": self._status_label(score),
            })
        rows.sort(key=lambda row: row["score"], reverse=True)
        return rows

    def _quest_score(self, quest_id: int) -> int:
        burst_count = self.session.scalar(
            select(func.count(Burst.id)).where(
                Burst.quest_id == quest_id,
                Burst.created_at >= self.cutoff,
            )
        ) or 0
        artifact_count = self.session.scalar(
            select(func.count(Relationship.id)).where(
                Relationship.source_type == "artifact",
                Relationship.target_type == "quest",
                Relationship.target_id == quest_id,
                Relationship.created_at >= self.cutoff,
            )
        ) or 0
        return int(burst_count * 2 + artifact_count)

    def _field_score(self, field_id: int) -> int:
        quest_ids = list(
            self.session.scalars(select(Quest.id).where(Quest.field_id == field_id))
        )
        if not quest_ids:
            return 0
        burst_count = self.session.scalar(
            select(func.count(Burst.id))
            .join(Quest, Burst.quest_id == Quest.id)
            .where(Quest.field_id == field_id, Burst.created_at >= self.cutoff)
        ) or 0
        return int(burst_count)

    def _bar(self, score: int) -> str:
        filled = min(MAX_BAR, max(1, score)) if score > 0 else 0
        return "█" * filled + "░" * (MAX_BAR - filled)

    def _status_label(self, score: int) -> str:
        if score >= 8:
            return "hot"
        if score >= 3:
            return "active"
        if score >= 1:
            return "slow"
        return "dormant"