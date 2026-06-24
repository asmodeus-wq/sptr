from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Field, Path, Quest, Relationship
from sparktrack_core.services.momentum_service import MomentumService
from sparktrack_core.services.unified_feed_service import UnifiedFeedService
from sparktrack_core.services.workspace_service import WorkspaceScope


class FieldOverviewService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def snapshot(self, field_id: int) -> dict[str, object] | None:
        field = self.session.get(Field, field_id)
        if field is None:
            return None
        path = self.session.get(Path, field.path_id)

        active_quests = list(
            self.session.scalars(
                select(Quest).where(Quest.field_id == field_id, Quest.status == "Active")
            )
        )
        dormant_quests = []
        cutoff = datetime.now() - timedelta(days=14)
        for quest in active_quests:
            last = self.session.scalar(
                select(func.max(Burst.created_at)).where(Burst.quest_id == quest.id)
            )
            if last is None or last < cutoff:
                dormant_quests.append(quest)

        scope = WorkspaceScope(id=f"field:{field_id}", name=field.name, path_id=field.path_id, field_id=field_id)
        feed = UnifiedFeedService(self.session).feed(scope=scope, limit=15)

        artifact_ids = self.session.scalars(
            select(Relationship.source_id).where(
                Relationship.source_type == "artifact",
                Relationship.target_type == "field",
                Relationship.target_id == field_id,
            )
        )
        artifacts = [self.session.get(Artifact, aid) for aid in artifact_ids if self.session.get(Artifact, aid)]

        resources_consumed = self.session.scalar(
            select(func.count()).select_from(Relationship).where(
                Relationship.source_type == "resource",
            )
        ) or 0

        momentum = MomentumService(self.session)
        score = momentum._field_score(field_id)

        return {
            "field": field,
            "path": path,
            "active_quests": active_quests,
            "dormant_quests": dormant_quests,
            "recent_activity": feed,
            "artifacts": artifacts[:10],
            "resources_consumed": resources_consumed,
            "momentum_score": score,
            "momentum_bar": momentum._bar(score),
            "momentum_label": momentum._status_label(score),
        }