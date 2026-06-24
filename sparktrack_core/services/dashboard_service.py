from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Field, Quest, Season
from sparktrack_core.services.activity_service import ActivityService
from sparktrack_core.services.app_state import AppContext
from sparktrack_core.services.context_resolver import ContextResolver


class DashboardService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.activity = ActivityService(session)
        self.resolver = ContextResolver(session)

    def snapshot(self, context: AppContext) -> dict[str, object]:
        labels = self.resolver.labels(context)
        return {
            "context": labels,
            "total_bursts": self._count(Burst),
            "active_quests": self._count_by_status(Quest, "Active"),
            "active_fields": self._count_by_status(Field, "Active"),
            "current_season": labels["season"],
            "recent_bursts": self._recent_bursts(8),
            "recent_artifacts": self._recent_artifacts(8),
            "activity_feed": self.activity.recent_feed(limit=20),
            "timeline": self.activity.timeline(days=14),
            "counts": self.activity.entity_counts(),
        }

    def _count(self, model: type) -> int:
        return self.session.scalar(select(func.count(model.id))) or 0

    def _count_by_status(self, model: type, status: str) -> int:
        return (
            self.session.scalar(select(func.count(model.id)).where(model.status == status))
            or 0
        )

    def _recent_bursts(self, limit: int) -> list[dict[str, object]]:
        rows = self.session.scalars(select(Burst).order_by(Burst.id.desc()).limit(limit))
        return [{"id": row.id, "title": row.title, "minutes": row.duration_minutes} for row in rows]

    def _recent_artifacts(self, limit: int) -> list[dict[str, object]]:
        rows = self.session.scalars(select(Artifact).order_by(Artifact.id.desc()).limit(limit))
        return [{"id": row.id, "title": row.title, "type": row.type} for row in rows]

    def _current_season_name(self) -> str:
        season = self.session.scalar(select(Season).where(Season.active.is_(True)).limit(1))
        return season.name if season else "No active season"