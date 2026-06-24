from __future__ import annotations

from datetime import datetime  # noqa: F401 — used in _active_quests

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Burst, Field, Path, Quest
from sparktrack_core.services.momentum_service import MomentumService
from sparktrack_core.services.neglect_service import NeglectService
from sparktrack_core.services.unified_feed_service import UnifiedFeedService
from sparktrack_core.services.workspace_service import WorkspaceScope, WorkspaceService


class FocusService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.workspaces = WorkspaceService(session)
        self.feed = UnifiedFeedService(session)
        self.momentum = MomentumService(session)
        self.neglect = NeglectService(session)

    def snapshot(self, scope: WorkspaceScope) -> dict[str, object]:
        return {
            "active_quests": self._active_quests(scope),
            "today_feed": self.feed.feed(scope=scope, today_only=True, limit=30),
            "momentum_quests": self.momentum.quest_momentum(scope),
            "momentum_fields": self.momentum.field_momentum(scope),
            "neglect": self.neglect.detect(scope),
        }

    def _active_quests(self, scope: WorkspaceScope) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        quests = self.session.scalars(
            select(Quest).where(Quest.status == "Active").order_by(Quest.priority.desc(), Quest.id.desc())
        )
        for quest in quests:
            field = self.session.get(Field, quest.field_id)
            if field is None:
                continue
            path = self.session.get(Path, field.path_id)
            if path is None:
                continue
            if not self.workspaces.quest_belongs(field.id, path.id, scope):
                continue

            burst_count = self.session.scalar(
                select(func.count(Burst.id)).where(Burst.quest_id == quest.id)
            ) or 0
            last_burst = self.session.scalar(
                select(func.max(Burst.created_at)).where(Burst.quest_id == quest.id)
            )
            momentum = MomentumService(self.session)
            score = momentum._quest_score(quest.id)

            days_since = 999 if last_burst is None else max(0, (datetime.now() - last_burst).days)
            rows.append({
                "id": quest.id,
                "title": quest.title,
                "path_name": path.name,
                "field_name": field.name,
                "priority": quest.priority,
                "burst_count": burst_count,
                "last_activity": last_burst,
                "days_since": days_since,
                "progress_label": self._progress_label(burst_count, score),
                "momentum_bar": momentum._bar(score),
                "momentum_label": momentum._status_label(score),
            })
        return rows

    def _progress_label(self, burst_count: int, score: int) -> str:
        if score >= 8:
            return f"Strong · {burst_count} bursts"
        if score >= 3:
            return f"Building · {burst_count} bursts"
        if burst_count:
            return f"Started · {burst_count} bursts"
        return "Not started"