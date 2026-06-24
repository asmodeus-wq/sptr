from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Field, Path, Principle, Quest, Relationship, Resource
from sparktrack_core.services.momentum_service import MomentumService
from sparktrack_core.services.unified_feed_service import UnifiedFeedService


class QuestCockpitService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def snapshot(self, quest_id: int) -> dict[str, object] | None:
        quest = self.session.get(Quest, quest_id)
        if quest is None:
            return None
        field = self.session.get(Field, quest.field_id)
        path = self.session.get(Path, field.path_id) if field else None

        bursts = list(
            self.session.scalars(
                select(Burst).where(Burst.quest_id == quest_id).order_by(Burst.id.desc()).limit(12)
            )
        )
        artifacts = self._linked_artifacts(quest_id)
        principles = self._linked_principles(quest_id)
        resources = self._linked_resources(artifacts)

        momentum = MomentumService(self.session)
        score = momentum._quest_score(quest_id)

        feed_service = UnifiedFeedService(self.session)
        from sparktrack_core.services.workspace_service import WorkspaceScope

        all_scope = WorkspaceScope(id="all", name="All")
        history = [
            event for event in feed_service.feed(scope=all_scope, limit=50)
            if event.get("quest_id") == quest_id
        ]

        return {
            "quest": quest,
            "field": field,
            "path": path,
            "bursts": bursts,
            "artifacts": artifacts,
            "principles": principles,
            "resources": resources,
            "momentum_score": score,
            "momentum_bar": momentum._bar(score),
            "momentum_label": momentum._status_label(score),
            "history": history[:20],
            "burst_count": len(bursts),
        }

    def _linked_artifacts(self, quest_id: int) -> list[Artifact]:
        ids = self.session.scalars(
            select(Relationship.source_id).where(
                Relationship.source_type == "artifact",
                Relationship.target_type == "quest",
                Relationship.target_id == quest_id,
            )
        )
        return [self.session.get(Artifact, artifact_id) for artifact_id in ids if self.session.get(Artifact, artifact_id)]

    def _linked_principles(self, quest_id: int) -> list[Principle]:
        ids = self.session.scalars(
            select(Relationship.target_id).where(
                Relationship.source_type == "quest",
                Relationship.source_id == quest_id,
                Relationship.target_type == "principle",
            )
        )
        return [self.session.get(Principle, pid) for pid in ids if self.session.get(Principle, pid)]

    def _linked_resources(self, artifacts: list[Artifact]) -> list[Resource]:
        resources: list[Resource] = []
        for artifact in artifacts:
            ids = self.session.scalars(
                select(Relationship.source_id).where(
                    Relationship.source_type == "resource",
                    Relationship.target_type == "artifact",
                    Relationship.target_id == artifact.id,
                )
            )
            for resource_id in ids:
                resource = self.session.get(Resource, resource_id)
                if resource and resource not in resources:
                    resources.append(resource)
        return resources