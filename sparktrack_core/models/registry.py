from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from sparktrack_core.models import (
    Artifact,
    Burst,
    Field,
    Path,
    Principle,
    Quest,
    Resource,
    Season,
)


@dataclass(frozen=True)
class EntityMeta:
    key: str
    label: str
    model: type
    title_field: str
    search_fields: tuple[str, ...]
    navigable: bool = True


ENTITY_REGISTRY: dict[str, EntityMeta] = {
    "path": EntityMeta("path", "Path", Path, "name", ("name", "description")),
    "field": EntityMeta("field", "Field", Field, "name", ("name", "description", "status")),
    "quest": EntityMeta("quest", "Quest", Quest, "title", ("title", "description", "status")),
    "burst": EntityMeta("burst", "Burst", Burst, "title", ("title", "notes")),
    "artifact": EntityMeta("artifact", "Artifact", Artifact, "title", ("title", "content", "type")),
    "resource": EntityMeta("resource", "Resource", Resource, "title", ("title", "source", "notes", "type")),
    "principle": EntityMeta("principle", "Principle", Principle, "statement", ("statement", "description")),
    "season": EntityMeta("season", "Season", Season, "name", ("name", "description")),
}

RELATIONSHIP_RULES: dict[tuple[str, str], str] = {
    ("artifact", "path"): "belongs_to",
    ("artifact", "field"): "belongs_to",
    ("artifact", "quest"): "supports",
    ("artifact", "principle"): "embodies",
    ("resource", "artifact"): "informs",
    ("quest", "principle"): "guided_by",
}

CAPTURE_TYPES: dict[str, tuple[str, str]] = {
    "burst": ("burst", "Burst"),
    "idea": ("artifact", "Idea"),
    "reflection": ("artifact", "Reflection"),
    "artifact": ("artifact", "Research Note"),
    "resource": ("resource", "Article"),
}


def entity_title(entity_type: str, row: object) -> str:
    meta = ENTITY_REGISTRY[entity_type]
    return str(getattr(row, meta.title_field, "") or f"{meta.label} #{getattr(row, 'id', '?')}")


def resolve_relationship_type(source_type: str, target_type: str) -> str | None:
    return RELATIONSHIP_RULES.get((source_type, target_type))