from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Field, Path, Quest, Resource


class ActivityService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def recent_feed(self, *, limit: int = 30) -> list[dict[str, object]]:
        events: list[dict[str, object]] = []

        for row in self.session.scalars(select(Burst).order_by(Burst.id.desc()).limit(limit)):
            events.append(
                {
                    "timestamp": row.start_time or row.created_at,
                    "entity_type": "burst",
                    "entity_id": row.id,
                    "title": row.title,
                    "summary": f"{row.duration_minutes} min burst",
                }
            )

        for row in self.session.scalars(select(Artifact).order_by(Artifact.id.desc()).limit(limit)):
            events.append(
                {
                    "timestamp": row.created_at,
                    "entity_type": "artifact",
                    "entity_id": row.id,
                    "title": row.title,
                    "summary": row.type,
                }
            )

        for row in self.session.scalars(select(Resource).order_by(Resource.id.desc()).limit(limit)):
            timestamp = getattr(row, "created_at", None) or datetime.min
            events.append(
                {
                    "timestamp": timestamp,
                    "entity_type": "resource",
                    "entity_id": row.id,
                    "title": row.title,
                    "summary": row.type,
                }
            )

        for row in self.session.scalars(select(Quest).order_by(Quest.id.desc()).limit(limit // 2)):
            events.append(
                {
                    "timestamp": row.created_at,
                    "entity_type": "quest",
                    "entity_id": row.id,
                    "title": row.title,
                    "summary": row.status,
                }
            )

        events.sort(key=lambda item: item["timestamp"] or datetime.min, reverse=True)
        return events[:limit]

    def timeline(self, *, days: int = 14) -> list[dict[str, object]]:
        feed = self.recent_feed(limit=200)
        return feed[: max(days * 3, 20)]

    def entity_counts(self) -> dict[str, int]:
        return {
            "paths": self._count(Path),
            "fields": self._count(Field),
            "quests": self._count(Quest),
            "bursts": self._count(Burst),
            "artifacts": self._count(Artifact),
            "resources": self._count(Resource),
        }

    def _count(self, model: type) -> int:
        return self.session.scalar(select(func.count(model.id))) or 0