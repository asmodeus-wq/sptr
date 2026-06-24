from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Field, Path, Quest
from sparktrack_core.services.workspace_service import WorkspaceScope, WorkspaceService


@dataclass(frozen=True)
class QuestAttention:
    id: int
    title: str
    field_name: str
    path_name: str
    priority: str
    status: str
    burst_count: int
    last_activity: datetime | None
    days_since_activity: int | None


@dataclass(frozen=True)
class FieldAttention:
    id: int
    name: str
    path_name: str
    active_quest_count: int
    burst_count: int
    last_activity: datetime | None
    days_since_activity: int | None


@dataclass(frozen=True)
class ActivityReference:
    id: int
    title: str
    entity_type: str
    timestamp: datetime | None
    context: str = ""


@dataclass(frozen=True)
class AttentionSummary:
    recently_active_quests: list[QuestAttention] = field(default_factory=list)
    dormant_quests: list[QuestAttention] = field(default_factory=list)
    most_active_fields: list[FieldAttention] = field(default_factory=list)
    neglected_fields: list[FieldAttention] = field(default_factory=list)
    recent_bursts: list[ActivityReference] = field(default_factory=list)
    recent_artifacts: list[ActivityReference] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "recently_active_quests": [item.__dict__ for item in self.recently_active_quests],
            "dormant_quests": [item.__dict__ for item in self.dormant_quests],
            "most_active_fields": [item.__dict__ for item in self.most_active_fields],
            "neglected_fields": [item.__dict__ for item in self.neglected_fields],
            "recent_bursts": [item.__dict__ for item in self.recent_bursts],
            "recent_artifacts": [item.__dict__ for item in self.recent_artifacts],
        }


class AttentionEngine:
    """Calculates reusable attention signals without making UI decisions."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.workspaces = WorkspaceService(session)

    def summarize(
        self,
        scope: WorkspaceScope,
        *,
        recent_days: int = 14,
        dormant_days: int = 21,
        limit: int = 8,
    ) -> AttentionSummary:
        quests = self._quest_attention(scope)
        fields = self._field_attention(scope)

        return AttentionSummary(
            recently_active_quests=[
                quest
                for quest in sorted(
                    quests,
                    key=lambda item: item.last_activity or datetime.min,
                    reverse=True,
                )
                if self._within_days(quest.last_activity, recent_days)
            ][:limit],
            dormant_quests=[
                quest
                for quest in sorted(
                    quests,
                    key=lambda item: item.days_since_activity or 9999,
                    reverse=True,
                )
                if quest.status == "Active"
                and (
                    quest.last_activity is None
                    or (quest.days_since_activity is not None and quest.days_since_activity >= dormant_days)
                )
            ][:limit],
            most_active_fields=sorted(
                fields,
                key=lambda item: (item.burst_count, item.last_activity or datetime.min),
                reverse=True,
            )[:limit],
            neglected_fields=[
                field_item
                for field_item in sorted(
                    fields,
                    key=lambda item: item.days_since_activity or 9999,
                    reverse=True,
                )
                if field_item.active_quest_count > 0
                and (
                    field_item.last_activity is None
                    or (
                        field_item.days_since_activity is not None
                        and field_item.days_since_activity >= dormant_days
                    )
                )
            ][:limit],
            recent_bursts=self._recent_bursts(scope, limit),
            recent_artifacts=self._recent_artifacts(limit),
        )

    def _quest_attention(self, scope: WorkspaceScope) -> list[QuestAttention]:
        rows: list[QuestAttention] = []
        quests = self.session.scalars(select(Quest).order_by(Quest.id.desc()))
        for quest in quests:
            field_item = self.session.get(Field, quest.field_id)
            if field_item is None:
                continue
            path = self.session.get(Path, field_item.path_id)
            if path is None or not self.workspaces.quest_belongs(field_item.id, path.id, scope):
                continue
            burst_count = self.session.scalar(
                select(func.count(Burst.id)).where(Burst.quest_id == quest.id)
            ) or 0
            last_activity = self.session.scalar(
                select(func.max(Burst.start_time)).where(Burst.quest_id == quest.id)
            ) or self.session.scalar(
                select(func.max(Burst.created_at)).where(Burst.quest_id == quest.id)
            )
            rows.append(
                QuestAttention(
                    id=quest.id,
                    title=quest.title,
                    field_name=field_item.name,
                    path_name=path.name,
                    priority=quest.priority,
                    status=quest.status,
                    burst_count=burst_count,
                    last_activity=last_activity,
                    days_since_activity=self._days_since(last_activity),
                )
            )
        return rows

    def _field_attention(self, scope: WorkspaceScope) -> list[FieldAttention]:
        rows: list[FieldAttention] = []
        fields = self.session.scalars(select(Field).order_by(Field.name))
        for field_item in fields:
            path = self.session.get(Path, field_item.path_id)
            if path is None or not self.workspaces.field_belongs(field_item.id, path.id, scope):
                continue
            quest_ids = list(
                self.session.scalars(
                    select(Quest.id).where(
                        Quest.field_id == field_item.id,
                        Quest.status == "Active",
                    )
                )
            )
            burst_count = 0
            last_activity = None
            if quest_ids:
                burst_count = self.session.scalar(
                    select(func.count(Burst.id)).where(Burst.quest_id.in_(quest_ids))
                ) or 0
                last_activity = self.session.scalar(
                    select(func.max(Burst.start_time)).where(Burst.quest_id.in_(quest_ids))
                ) or self.session.scalar(
                    select(func.max(Burst.created_at)).where(Burst.quest_id.in_(quest_ids))
                )
            rows.append(
                FieldAttention(
                    id=field_item.id,
                    name=field_item.name,
                    path_name=path.name,
                    active_quest_count=len(quest_ids),
                    burst_count=burst_count,
                    last_activity=last_activity,
                    days_since_activity=self._days_since(last_activity),
                )
            )
        return rows

    def _recent_bursts(self, scope: WorkspaceScope, limit: int) -> list[ActivityReference]:
        rows: list[ActivityReference] = []
        bursts = self.session.scalars(select(Burst).order_by(Burst.id.desc()).limit(limit * 3))
        for burst in bursts:
            quest = self.session.get(Quest, burst.quest_id)
            if quest is None:
                continue
            field_item = self.session.get(Field, quest.field_id)
            if field_item is None:
                continue
            path = self.session.get(Path, field_item.path_id)
            if path is None or not self.workspaces.quest_belongs(field_item.id, path.id, scope):
                continue
            rows.append(
                ActivityReference(
                    id=burst.id,
                    title=burst.title,
                    entity_type="burst",
                    timestamp=burst.start_time or burst.created_at,
                    context=f"{path.name} / {field_item.name} / {quest.title}",
                )
            )
            if len(rows) >= limit:
                break
        return rows

    def _recent_artifacts(self, limit: int) -> list[ActivityReference]:
        artifacts = self.session.scalars(select(Artifact).order_by(Artifact.id.desc()).limit(limit))
        return [
            ActivityReference(
                id=artifact.id,
                title=artifact.title,
                entity_type="artifact",
                timestamp=artifact.created_at,
                context=artifact.type,
            )
            for artifact in artifacts
        ]

    def _within_days(self, timestamp: datetime | None, days: int) -> bool:
        if timestamp is None:
            return False
        return timestamp >= datetime.now() - timedelta(days=days)

    def _days_since(self, timestamp: datetime | None) -> int | None:
        if timestamp is None:
            return None
        return max(0, (datetime.now() - timestamp).days)
