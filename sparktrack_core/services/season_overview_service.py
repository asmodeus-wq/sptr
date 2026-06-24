from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Field, Path, Quest, Season
from sparktrack_core.services.unified_feed_service import UnifiedFeedService
from sparktrack_core.services.workspace_service import WorkspaceScope


class SeasonOverviewService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def snapshot(self, season_id: int) -> dict[str, object] | None:
        season = self.session.get(Season, season_id)
        if season is None:
            return None

        burst_count = self.session.scalar(select(func.count(Burst.id))) or 0
        artifact_count = self.session.scalar(select(func.count(Artifact.id))) or 0
        active_quests = list(self.session.scalars(select(Quest).where(Quest.status == "Active")))
        paths = list(self.session.scalars(select(Path)))
        fields = list(self.session.scalars(select(Field)))

        reflections = list(
            self.session.scalars(
                select(Artifact).where(Artifact.type == "Reflection").order_by(Artifact.id.desc()).limit(8)
            )
        )

        feed = UnifiedFeedService(self.session).feed(
            scope=WorkspaceScope(id="all", name="All"),
            limit=30,
        )

        return {
            "season": season,
            "goals": season.description,
            "paths": paths,
            "fields": fields,
            "active_quests": active_quests,
            "quest_progress": [
                {
                    "id": quest.id,
                    "title": quest.title,
                    "status": quest.status,
                    "burst_count": self.session.scalar(
                        select(func.count(Burst.id)).where(Burst.quest_id == quest.id)
                    ) or 0,
                }
                for quest in active_quests[:12]
            ],
            "artifacts_created": artifact_count,
            "bursts_created": burst_count,
            "reflections": reflections,
            "timeline": feed,
        }