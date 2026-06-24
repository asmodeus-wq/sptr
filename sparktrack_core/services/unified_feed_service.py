from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Field, Path, Quest, Relationship, Resource
from sparktrack_core.services.workspace_service import WorkspaceScope, WorkspaceService


@dataclass(frozen=True)
class LifeFeedItem:
    timestamp: datetime | None
    entity_type: str
    entity_id: int
    title: str
    preview: str
    human_summary: str
    quest_id: int | None = None
    quest_title: str = "-"
    field_id: int | None = None
    field_name: str = "-"
    path_id: int | None = None
    path_name: str = "-"

    def as_dict(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "title": self.title,
            "preview": self.preview,
            "human_summary": self.human_summary,
            "quest_id": self.quest_id,
            "quest_title": self.quest_title,
            "field_id": self.field_id,
            "field_name": self.field_name,
            "path_id": self.path_id,
            "path_name": self.path_name,
        }


class UnifiedFeedService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.workspaces = WorkspaceService(session)

    def feed(
        self,
        *,
        scope: WorkspaceScope,
        today_only: bool = False,
        limit: int = 40,
    ) -> list[dict[str, object]]:
        return [
            item.as_dict()
            for item in self.feed_items(scope=scope, today_only=today_only, limit=limit)
        ]

    def feed_items(
        self,
        *,
        scope: WorkspaceScope,
        today_only: bool = False,
        limit: int = 40,
    ) -> list[LifeFeedItem]:
        events: list[LifeFeedItem] = []
        today = date.today()

        events.extend(self._burst_events(scope, today_only, today, limit))
        events.extend(self._artifact_events(scope, today_only, today, limit))
        events.extend(self._resource_events(scope, today_only, today, limit))
        events.extend(self._quest_events(scope, today_only, today, limit))

        events.sort(key=lambda row: row.timestamp or datetime.min, reverse=True)
        return events[:limit]

    def _burst_events(
        self,
        scope: WorkspaceScope,
        today_only: bool,
        today: date,
        limit: int,
    ) -> list[LifeFeedItem]:
        events: list[LifeFeedItem] = []
        for burst in self.session.scalars(select(Burst).order_by(Burst.id.desc()).limit(limit * 2)):
            quest = self.session.get(Quest, burst.quest_id)
            if quest is None:
                continue
            field = self.session.get(Field, quest.field_id)
            if field is None:
                continue
            path = self.session.get(Path, field.path_id)
            if path is None or not self.workspaces.quest_belongs(field.id, path.id, scope):
                continue
            timestamp = burst.start_time or burst.created_at
            if today_only and not self._is_today(timestamp, today):
                continue
            preview = burst.notes[:120] if burst.notes else f"{burst.duration_minutes} min"
            events.append(
                LifeFeedItem(
                    timestamp=timestamp,
                    entity_type="burst",
                    entity_id=burst.id,
                    title=burst.title,
                    preview=preview,
                    human_summary=f"Focused on {quest.title}",
                    quest_id=quest.id,
                    quest_title=quest.title,
                    field_id=field.id,
                    field_name=field.name,
                    path_id=path.id,
                    path_name=path.name,
                )
            )
        return events

    def _artifact_events(
        self,
        scope: WorkspaceScope,
        today_only: bool,
        today: date,
        limit: int,
    ) -> list[LifeFeedItem]:
        events: list[LifeFeedItem] = []
        for artifact in self.session.scalars(select(Artifact).order_by(Artifact.id.desc()).limit(limit * 2)):
            context = self._artifact_context(artifact.id) or {}
            if context and not self._context_in_scope(context, scope):
                continue
            timestamp = artifact.created_at
            if today_only and not self._is_today(timestamp, today):
                continue
            events.append(
                LifeFeedItem(
                    timestamp=timestamp,
                    entity_type="artifact",
                    entity_id=artifact.id,
                    title=artifact.title,
                    preview=artifact.content[:120] if artifact.content else artifact.type,
                    human_summary=f"Captured {artifact.type.lower()}: {artifact.title}",
                    quest_id=context.get("quest_id"),
                    quest_title=str(context.get("quest_title", "-")),
                    field_id=context.get("field_id"),
                    field_name=str(context.get("field_name", "-")),
                    path_id=context.get("path_id"),
                    path_name=str(context.get("path_name", "-")),
                )
            )
        return events

    def _resource_events(
        self,
        scope: WorkspaceScope,
        today_only: bool,
        today: date,
        limit: int,
    ) -> list[LifeFeedItem]:
        if scope.is_filtered:
            return []
        events: list[LifeFeedItem] = []
        for resource in self.session.scalars(select(Resource).order_by(Resource.id.desc()).limit(limit * 2)):
            timestamp = resource.created_at
            if today_only and not self._is_today(timestamp, today):
                continue
            events.append(
                LifeFeedItem(
                    timestamp=timestamp,
                    entity_type="resource",
                    entity_id=resource.id,
                    title=resource.title,
                    preview=resource.notes[:120] if resource.notes else resource.type,
                    human_summary=f"Added resource: {resource.title}",
                )
            )
        return events

    def _quest_events(
        self,
        scope: WorkspaceScope,
        today_only: bool,
        today: date,
        limit: int,
    ) -> list[LifeFeedItem]:
        events: list[LifeFeedItem] = []
        for quest in self.session.scalars(select(Quest).order_by(Quest.id.desc()).limit(limit)):
            field = self.session.get(Field, quest.field_id)
            if field is None:
                continue
            path = self.session.get(Path, field.path_id)
            if path is None or not self.workspaces.quest_belongs(field.id, path.id, scope):
                continue
            timestamp = quest.created_at
            if today_only and not self._is_today(timestamp, today):
                continue
            events.append(
                LifeFeedItem(
                    timestamp=timestamp,
                    entity_type="quest",
                    entity_id=quest.id,
                    title=quest.title,
                    preview=quest.status,
                    human_summary=f"Quest updated: {quest.title} ({quest.status})",
                    quest_id=quest.id,
                    quest_title=quest.title,
                    field_id=field.id,
                    field_name=field.name,
                    path_id=path.id,
                    path_name=path.name,
                )
            )
        return events

    def _is_today(self, timestamp: datetime | None, today: date) -> bool:
        if timestamp is None:
            return False
        return timestamp.date() == today

    def _artifact_context(self, artifact_id: int) -> dict[str, object] | None:
        rows = self.session.scalars(
            select(Relationship).where(
                Relationship.source_type == "artifact",
                Relationship.source_id == artifact_id,
            )
        )
        context: dict[str, object] = {}
        for row in rows:
            if row.target_type == "quest":
                quest = self.session.get(Quest, row.target_id)
                if quest:
                    context["quest_id"] = quest.id
                    context["quest_title"] = quest.title
                    field = self.session.get(Field, quest.field_id)
                    if field:
                        context["field_id"] = field.id
                        context["field_name"] = field.name
                        path = self.session.get(Path, field.path_id)
                        if path:
                            context["path_id"] = path.id
                            context["path_name"] = path.name
            elif row.target_type == "field" and "field_id" not in context:
                field = self.session.get(Field, row.target_id)
                if field:
                    context["field_id"] = field.id
                    context["field_name"] = field.name
                    path = self.session.get(Path, field.path_id)
                    if path:
                        context["path_id"] = path.id
                        context["path_name"] = path.name
            elif row.target_type == "path" and "path_id" not in context:
                path = self.session.get(Path, row.target_id)
                if path:
                    context["path_id"] = path.id
                    context["path_name"] = path.name
        return context or None

    def _context_in_scope(self, context: dict[str, object], scope: WorkspaceScope) -> bool:
        if not scope.is_filtered:
            return True
        if scope.field_id is not None:
            return context.get("field_id") == scope.field_id
        if scope.path_id is not None:
            return context.get("path_id") == scope.path_id
        return True
