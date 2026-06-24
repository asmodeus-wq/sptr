from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from sparktrack_core.models import Season
from sparktrack_core.services.app_state import AppContext
from sparktrack_core.services.attention_engine import AttentionEngine, AttentionSummary
from sparktrack_core.services.unified_feed_service import UnifiedFeedService
from sparktrack_core.services.workspace_service import WorkspaceScope


@dataclass(frozen=True)
class TodayContext:
    workspace_id: str
    workspace_name: str
    season_name: str
    active_context: dict[str, int | None]
    attention: AttentionSummary
    life_feed: list[dict[str, object]] = field(default_factory=list)

    @property
    def matters_now(self) -> list[str]:
        items: list[str] = []
        items.extend(quest.title for quest in self.attention.recently_active_quests[:3])
        items.extend(quest.title for quest in self.attention.dormant_quests[:2])
        return items[:5]

    def as_dict(self) -> dict[str, object]:
        return {
            "workspace_id": self.workspace_id,
            "workspace_name": self.workspace_name,
            "season_name": self.season_name,
            "active_context": self.active_context,
            "attention": self.attention.as_dict(),
            "life_feed": self.life_feed,
            "matters_now": self.matters_now,
        }


class TodayService:
    """Single source of truth for what matters today."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.attention = AttentionEngine(session)
        self.feed = UnifiedFeedService(session)

    def context(self, scope: WorkspaceScope, app_context: AppContext) -> TodayContext:
        attention = self.attention.summarize(scope)
        return TodayContext(
            workspace_id=scope.id,
            workspace_name=scope.name,
            season_name=self._season_name(app_context),
            active_context=app_context.as_dict(),
            attention=attention,
            life_feed=self.feed.feed(scope=scope, limit=20),
        )

    def _season_name(self, app_context: AppContext) -> str:
        if app_context.season_id is not None:
            season = self.session.get(Season, app_context.season_id)
            if season:
                return season.name
        active = self.session.scalar(select(Season).where(Season.active.is_(True)).limit(1))
        return active.name if active else "No active season"
