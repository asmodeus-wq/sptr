from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Resource
from sparktrack_core.models.registry import CAPTURE_TYPES
from sparktrack_core.services.app_state import AppContext
from sparktrack_core.services.context_resolver import ContextResolver
from sparktrack_core.services.relationship_service import RelationshipService


class CaptureService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.resolver = ContextResolver(session)
        self.relationships = RelationshipService(session)

    def capture(self, capture_type: str, title: str, body: str, context: AppContext) -> tuple[str, int]:
        if capture_type not in CAPTURE_TYPES:
            raise ValueError(f"Unknown capture type: {capture_type}")

        entity_kind, default_subtype = CAPTURE_TYPES[capture_type]
        title = title.strip()
        body = body.strip()
        if not title:
            raise ValueError("Title is required.")

        if entity_kind == "burst":
            quest_id = self.resolver.resolve_quest_id(context)
            row = Burst(
                quest_id=quest_id,
                title=title,
                notes=body,
                duration_minutes=25,
                start_time=datetime.now(),
            )
            self.session.add(row)
            self.session.flush()
            return "burst", row.id

        if entity_kind == "artifact":
            row = Artifact(type=default_subtype, title=title, content=body)
            self.session.add(row)
            self.session.flush()
            self.relationships.auto_link_context(
                entity_type="artifact",
                entity_id=row.id,
                path_id=context.path_id,
                field_id=context.field_id,
                quest_id=context.quest_id,
            )
            return "artifact", row.id

        row = Resource(title=title, type=default_subtype, notes=body, source="", progress="Reference")
        self.session.add(row)
        self.session.flush()
        return "resource", row.id