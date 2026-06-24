from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Burst, Field, Path, Quest
from sparktrack_core.models.registry import ENTITY_REGISTRY, entity_title
from sparktrack_core.services.workspace_service import WorkspaceScope, WorkspaceService


@dataclass(frozen=True)
class SearchResult:
    entity_type: str
    entity_id: int
    title: str
    subtitle: str
    score: int


class SearchService:
    """Local keyword search with a semantic-search-ready result contract."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def search(
        self,
        query: str,
        *,
        scope: WorkspaceScope | None = None,
        limit: int = 50,
    ) -> list[SearchResult]:
        needle = query.strip().lower()
        if not needle:
            return []

        workspace = WorkspaceService(self.session)
        active_scope = scope or WorkspaceService.ALL

        results: list[SearchResult] = []
        for entity_type, meta in ENTITY_REGISTRY.items():
            clauses = []
            for field_name in meta.search_fields:
                column = getattr(meta.model, field_name)
                clauses.append(column.ilike(f"%{needle}%"))
            if not clauses:
                continue

            rows = self.session.scalars(
                select(meta.model).where(or_(*clauses)).order_by(meta.model.id.desc()).limit(limit * 3)
            )
            for row in rows:
                if not self._in_workspace(entity_type, row, active_scope, workspace):
                    continue
                title = entity_title(entity_type, row)
                subtitle = self._subtitle(entity_type, row)
                score = self._score(needle, title, subtitle)
                results.append(
                    SearchResult(
                        entity_type=entity_type,
                        entity_id=row.id,
                        title=title,
                        subtitle=subtitle,
                        score=score,
                    )
                )

        results.sort(key=lambda item: (-item.score, item.title.lower()))
        return results[:limit]

    def _in_workspace(
        self,
        entity_type: str,
        row: object,
        scope: WorkspaceScope,
        workspace: WorkspaceService,
    ) -> bool:
        if not scope.is_filtered:
            return True
        if entity_type == "quest":
            field = self.session.get(Field, row.field_id)
            path = self.session.get(Path, field.path_id) if field else None
            return field is not None and path is not None and workspace.quest_belongs(field.id, path.id, scope)
        if entity_type == "field":
            return workspace.field_belongs(row.id, row.path_id, scope)
        if entity_type == "path":
            return scope.path_id is None or row.id == scope.path_id
        if entity_type == "burst":
            quest = self.session.get(Quest, row.quest_id)
            if quest is None:
                return False
            field = self.session.get(Field, quest.field_id)
            path = self.session.get(Path, field.path_id) if field else None
            return field is not None and path is not None and workspace.quest_belongs(field.id, path.id, scope)
        if entity_type in {"artifact", "resource", "principle", "season"}:
            return not scope.is_filtered or entity_type in {"artifact"}
        return True

    def _subtitle(self, entity_type: str, row: object) -> str:
        if entity_type == "artifact":
            return str(getattr(row, "type", ""))
        if entity_type == "resource":
            return str(getattr(row, "type", ""))
        if entity_type == "quest":
            return str(getattr(row, "status", ""))
        if entity_type == "field":
            return str(getattr(row, "status", ""))
        return entity_type.replace("_", " ").title()

    def _score(self, needle: str, title: str, subtitle: str) -> int:
        title_lower = title.lower()
        subtitle_lower = subtitle.lower()
        if title_lower == needle:
            return 100
        if title_lower.startswith(needle):
            return 80
        if needle in title_lower:
            return 60
        if needle in subtitle_lower:
            return 40
        return 20