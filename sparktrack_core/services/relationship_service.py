from __future__ import annotations

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Relationship
from sparktrack_core.models.registry import ENTITY_REGISTRY, entity_title, resolve_relationship_type


class RelationshipService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def link(self, source_type: str, source_id: int, target_type: str, target_id: int) -> Relationship:
        relationship_type = resolve_relationship_type(source_type, target_type)
        if relationship_type is None:
            raise ValueError(f"Unsupported link: {source_type} -> {target_type}")

        existing = self.session.scalar(
            select(Relationship).where(
                Relationship.source_type == source_type,
                Relationship.source_id == source_id,
                Relationship.target_type == target_type,
                Relationship.target_id == target_id,
            )
        )
        if existing is not None:
            return existing

        row = Relationship(
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            relationship_type=relationship_type,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def unlink(self, source_type: str, source_id: int, target_type: str, target_id: int) -> bool:
        row = self.session.scalar(
            select(Relationship).where(
                Relationship.source_type == source_type,
                Relationship.source_id == source_id,
                Relationship.target_type == target_type,
                Relationship.target_id == target_id,
            )
        )
        if row is None:
            return False
        self.session.delete(row)
        self.session.flush()
        return True

    def list_for_entity(self, entity_type: str, entity_id: int) -> list[dict[str, object]]:
        rows = self.session.scalars(
            select(Relationship).where(
                or_(
                    and_(
                        Relationship.source_type == entity_type,
                        Relationship.source_id == entity_id,
                    ),
                    and_(
                        Relationship.target_type == entity_type,
                        Relationship.target_id == entity_id,
                    ),
                )
            )
        )
        results: list[dict[str, object]] = []
        for row in rows:
            if row.source_type == entity_type and row.source_id == entity_id:
                other_type, other_id = row.target_type, row.target_id
                direction = "outgoing"
            else:
                other_type, other_id = row.source_type, row.source_id
                direction = "incoming"

            meta = ENTITY_REGISTRY.get(other_type)
            title = f"{other_type} #{other_id}"
            if meta is not None:
                other = self.session.get(meta.model, other_id)
                if other is not None:
                    title = entity_title(other_type, other)

            results.append(
                {
                    "relationship_id": row.id,
                    "relationship_type": row.relationship_type,
                    "direction": direction,
                    "entity_type": other_type,
                    "entity_id": other_id,
                    "title": title,
                }
            )
        return results

    def auto_link_context(
        self,
        *,
        entity_type: str,
        entity_id: int,
        path_id: int | None,
        field_id: int | None,
        quest_id: int | None,
    ) -> None:
        if entity_type != "artifact":
            return
        if path_id:
            self.link("artifact", entity_id, "path", path_id)
        if field_id:
            self.link("artifact", entity_id, "field", field_id)
        if quest_id:
            self.link("artifact", entity_id, "quest", quest_id)