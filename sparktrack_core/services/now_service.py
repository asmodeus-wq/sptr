from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Quest
from sparktrack_core.services.app_state import AppContext
from sparktrack_core.services.context_resolver import ContextResolver
from sparktrack_core.services.feed_narrator import narrate_event
from sparktrack_core.services.focus_service import FocusService
from sparktrack_core.services.progress_service import ProgressService
from sparktrack_core.services.today_service import TodayService
from sparktrack_core.services.unified_feed_service import UnifiedFeedService
from sparktrack_core.services.workspace_service import WorkspaceScope


class NowService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.focus = FocusService(session)
        self.feed = UnifiedFeedService(session)
        self.progress = ProgressService(session)
        self.resolver = ContextResolver(session)
        self.today = TodayService(session)

    def snapshot(self, scope: WorkspaceScope, context: AppContext) -> dict[str, object]:
        focus_data = self.focus.snapshot(scope)
        labels = self.resolver.labels(context)
        today_context = self.today.context(scope, context)

        raw_feed = self.feed.feed(scope=scope, limit=25)
        narrated = [narrate_event(event) for event in raw_feed]

        today_raw = self.feed.feed(scope=scope, today_only=True, limit=20)
        today_narrated = [narrate_event(event) for event in today_raw]

        insights = self._recent_insights(scope)
        captures = today_narrated[:8]

        return {
            "current_focus": {
                "path": labels["path"],
                "field": labels["field"],
                "quest": labels["quest"],
                "season": labels["season"],
                "workspace": scope.name,
            },
            "today_context": today_context.as_dict(),
            "active_quests": focus_data["active_quests"],
            "recent_progress": narrated[:12],
            "needs_attention": focus_data["neglect"],
            "recent_insights": insights,
            "recent_captures": captures,
            "momentum_quests": focus_data["momentum_quests"],
            "momentum_fields": focus_data["momentum_fields"],
            "heatmap": self.progress.heatmap(scope),
            "quest_health": self.progress.quest_health(scope),
            "consistency": self.progress.consistency(scope),
            "upcoming_decisions": self.progress.upcoming_decisions(scope),
        }

    def _recent_insights(self, scope: WorkspaceScope) -> list[dict[str, object]]:
        insight_types = {"Reflection", "Idea", "Lesson", "Research Note", "Principle"}
        rows = []
        for artifact in self.session.scalars(
            select(Artifact).order_by(Artifact.id.desc()).limit(40)
        ):
            if artifact.type not in insight_types:
                continue
            event = {
                "entity_type": "artifact",
                "entity_id": artifact.id,
                "title": artifact.title,
                "preview": artifact.type,
                "timestamp": artifact.created_at,
                "quest_title": "—",
                "field_name": "—",
                "path_name": "—",
            }
            narrated = narrate_event(event)
            rows.append({
                "id": artifact.id,
                "headline": narrated["headline"],
                "type": artifact.type,
                "time_ago": narrated["time_ago"],
            })
            if len(rows) >= 8:
                break
        return rows
