from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Field, Path, Principle, Quest, Relationship, Resource, Season
from sparktrack_core.services.workspace_service import WorkspaceScope, WorkspaceService


VIEW_MODES = ["Recent", "Active", "Stalled", "Completed", "Most Linked", "Most Referenced", "Most Important"]


class SmartViewService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.workspaces = WorkspaceService(session)
        self.stall_cutoff = datetime.now() - timedelta(days=14)

    def list_items(
        self,
        entity_type: str,
        view_mode: str,
        scope: WorkspaceScope,
        *,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        if view_mode not in VIEW_MODES:
            view_mode = "Recent"

        if entity_type == "quest":
            return self._quest_views(view_mode, scope, limit)
        if entity_type == "field":
            return self._field_views(view_mode, scope, limit)
        if entity_type == "burst":
            return self._burst_views(view_mode, scope, limit)
        if entity_type == "artifact":
            return self._artifact_views(view_mode, scope, limit)
        if entity_type == "resource":
            return self._resource_views(view_mode, scope, limit)
        if entity_type == "season":
            return self._season_views(view_mode, limit)
        if entity_type == "principle":
            return self._principle_views(view_mode, limit)
        return []

    def _quest_views(self, mode: str, scope: WorkspaceScope, limit: int) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for quest in self.session.scalars(select(Quest)):
            field = self.session.get(Field, quest.field_id)
            if field is None:
                continue
            path = self.session.get(Path, field.path_id)
            if path is None or not self.workspaces.quest_belongs(field.id, path.id, scope):
                continue
            last = self.session.scalar(
                select(func.max(Burst.created_at)).where(Burst.quest_id == quest.id)
            )
            link_count = self.session.scalar(
                select(func.count(Relationship.id)).where(
                    or_(
                        (Relationship.source_type == "quest") & (Relationship.source_id == quest.id),
                        (Relationship.target_type == "quest") & (Relationship.target_id == quest.id),
                    )
                )
            ) or 0
            rows.append({
                "id": quest.id,
                "title": quest.title,
                "subtitle": f"{path.name} → {field.name}",
                "status": quest.status,
                "priority": quest.priority,
                "last_activity": last,
                "link_count": link_count,
                "created_at": quest.created_at,
            })

        if mode == "Active":
            rows = [row for row in rows if row["status"] == "Active"]
        elif mode == "Completed":
            rows = [row for row in rows if row["status"] == "Completed"]
        elif mode == "Stalled":
            rows = [
                row for row in rows
                if row["status"] == "Active"
                and (row["last_activity"] is None or row["last_activity"] < self.stall_cutoff)
            ]
        elif mode == "Most Linked":
            rows.sort(key=lambda row: row["link_count"], reverse=True)
        elif mode == "Most Important":
            priority_rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
            rows.sort(key=lambda row: priority_rank.get(str(row["priority"]), 0), reverse=True)
        else:
            rows.sort(key=lambda row: row["created_at"] or datetime.min, reverse=True)
        return rows[:limit]

    def _field_views(self, mode: str, scope: WorkspaceScope, limit: int) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for field in self.session.scalars(select(Field)):
            path = self.session.get(Path, field.path_id)
            if path is None or not self.workspaces.field_belongs(field.id, path.id, scope):
                continue
            last = self.session.scalar(
                select(func.max(Burst.created_at))
                .join(Quest, Burst.quest_id == Quest.id)
                .where(Quest.field_id == field.id)
            )
            rows.append({
                "id": field.id,
                "title": field.name,
                "subtitle": path.name,
                "status": field.status,
                "last_activity": last,
                "created_at": field.created_at,
            })
        if mode == "Active":
            rows = [row for row in rows if row["status"] == "Active"]
        elif mode == "Stalled":
            rows = [
                row for row in rows
                if row["status"] == "Active"
                and (row["last_activity"] is None or row["last_activity"] < self.stall_cutoff)
            ]
        else:
            rows.sort(key=lambda row: row["created_at"] or datetime.min, reverse=True)
        return rows[:limit]

    def _burst_views(self, mode: str, scope: WorkspaceScope, limit: int) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for burst in self.session.scalars(select(Burst)):
            quest = self.session.get(Quest, burst.quest_id)
            if quest is None:
                continue
            field = self.session.get(Field, quest.field_id)
            path = self.session.get(Path, field.path_id) if field else None
            if field is None or path is None or not self.workspaces.quest_belongs(field.id, path.id, scope):
                continue
            rows.append({
                "id": burst.id,
                "title": burst.title,
                "subtitle": f"{path.name} → {quest.title}",
                "created_at": burst.start_time or burst.created_at,
            })
        rows.sort(key=lambda row: row["created_at"] or datetime.min, reverse=True)
        return rows[:limit]

    def _artifact_views(self, mode: str, scope: WorkspaceScope, limit: int) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for artifact in self.session.scalars(select(Artifact)):
            link_count = self.session.scalar(
                select(func.count(Relationship.id)).where(
                    or_(
                        (Relationship.source_type == "artifact") & (Relationship.source_id == artifact.id),
                        (Relationship.target_type == "artifact") & (Relationship.target_id == artifact.id),
                    )
                )
            ) or 0
            ref_count = self.session.scalar(
                select(func.count(Relationship.id)).where(
                    Relationship.target_type == "artifact",
                    Relationship.target_id == artifact.id,
                )
            ) or 0
            rows.append({
                "id": artifact.id,
                "title": artifact.title,
                "subtitle": artifact.type,
                "link_count": link_count,
                "ref_count": ref_count,
                "created_at": artifact.created_at,
            })
        if mode == "Most Linked":
            rows.sort(key=lambda row: row["link_count"], reverse=True)
        elif mode == "Most Referenced":
            rows.sort(key=lambda row: row["ref_count"], reverse=True)
        else:
            rows.sort(key=lambda row: row["created_at"] or datetime.min, reverse=True)
        return rows[:limit]

    def _resource_views(self, mode: str, scope: WorkspaceScope, limit: int) -> list[dict[str, object]]:
        if scope.is_filtered:
            return []
        rows: list[dict[str, object]] = []
        for resource in self.session.scalars(select(Resource)):
            ref_count = self.session.scalar(
                select(func.count(Relationship.id)).where(
                    Relationship.source_type == "resource",
                    Relationship.source_id == resource.id,
                )
            ) or 0
            rows.append({
                "id": resource.id,
                "title": resource.title,
                "subtitle": resource.progress,
                "ref_count": ref_count,
                "created_at": resource.created_at,
            })
        if mode == "Most Referenced":
            rows.sort(key=lambda row: row["ref_count"], reverse=True)
        else:
            rows.sort(key=lambda row: row["created_at"] or datetime.min, reverse=True)
        return rows[:limit]

    def _season_views(self, mode: str, limit: int) -> list[dict[str, object]]:
        rows = [
            {
                "id": season.id,
                "title": season.name,
                "subtitle": "Active" if season.active else "Inactive",
                "created_at": season.created_at,
            }
            for season in self.session.scalars(select(Season))
        ]
        if mode == "Active":
            rows = [row for row in rows if row["subtitle"] == "Active"]
        rows.sort(key=lambda row: row["created_at"] or datetime.min, reverse=True)
        return rows[:limit]

    def _principle_views(self, mode: str, limit: int) -> list[dict[str, object]]:
        rows = [
            {
                "id": principle.id,
                "title": principle.statement,
                "subtitle": "Active" if principle.active else "Inactive",
                "created_at": principle.created_at,
            }
            for principle in self.session.scalars(select(Principle))
        ]
        if mode == "Active":
            rows = [row for row in rows if row["subtitle"] == "Active"]
        rows.sort(key=lambda row: row["created_at"] or datetime.min, reverse=True)
        return rows[:limit]