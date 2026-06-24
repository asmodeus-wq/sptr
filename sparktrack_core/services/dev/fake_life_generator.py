from __future__ import annotations

import random
from datetime import date, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from sparktrack_core.models import (
    Artifact,
    Burst,
    Field,
    Path,
    Principle,
    Quest,
    Relationship,
    Resource,
    Season,
)
from sparktrack_core.services.relationship_service import RelationshipService


PROFILES: dict[str, dict[str, object]] = {
    "builder": {
        "paths": ["Builder", "Steward"],
        "fields": ["SparkTrack", "Systems", "Ventures", "Home Ops"],
        "quests": [
            "Build SparkTrack Core",
            "Ship V1.5 Context Layer",
            "Design capture workflow",
            "Refactor repository layer",
        ],
        "artifact_types": ["Idea", "Research Note", "Lesson", "Concept"],
        "resources": ["Article", "Course", "Paper"],
        "principles": [
            "Ship small, learn fast",
            "Context before capture",
            "Local-first by default",
        ],
    },
    "warrior": {
        "paths": ["Warrior", "Steward"],
        "fields": ["Strength", "Mobility", "Recovery", "Nutrition"],
        "quests": ["Build base strength", "Improve VO2 max", "Sleep protocol", "Meal prep system"],
        "artifact_types": ["Observation", "Lesson", "Reflection"],
        "resources": ["Video", "Book", "Article"],
        "principles": ["Consistency beats intensity", "Recover as hard as you train"],
    },
    "philosopher": {
        "paths": ["Philosopher", "Householder"],
        "fields": ["Ethics", "Reflection", "Reading", "Dialogue"],
        "quests": ["Stoic morning practice", "Weekly review ritual", "Read primary texts"],
        "artifact_types": ["Reflection", "Quote", "Principle"],
        "resources": ["Book", "Paper", "Article"],
        "principles": ["Examine assumptions", "Write to think"],
    },
    "creator": {
        "paths": ["Creator", "Philosopher"],
        "fields": ["Writing", "Worldbuilding", "Sketching", "Editing"],
        "quests": ["Draft novella act I", "Character bible", "Daily sketch habit"],
        "artifact_types": ["Story Fragment", "Character Sketch", "Idea", "Concept"],
        "resources": ["Book", "Video", "Article"],
        "principles": ["Create before you consume", "Finish ugly drafts"],
    },
    "polymath": {
        "paths": ["Builder", "Warrior", "Philosopher", "Creator", "Steward", "Householder"],
        "fields": ["SparkTrack", "Strength", "Ethics", "Writing", "Home Ops", "Family"],
        "quests": [
            "Build SparkTrack Core",
            "Strength block",
            "Weekly reflection",
            "Draft scene",
            "Family planning",
        ],
        "artifact_types": ["Idea", "Reflection", "Lesson", "Research Note", "Story Fragment"],
        "resources": ["Book", "Course", "Article", "Paper", "Video"],
        "principles": [
            "Integrate, don't fragment",
            "Seasonal focus",
            "Capture everything once",
        ],
    },
}


class FakeLifeGenerator:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.random = random.Random(42)

    def clear_all(self) -> None:
        for model in [Relationship, Burst, Artifact, Resource, Quest, Field, Principle, Season, Path]:
            self.session.execute(delete(model))
        self.session.flush()

    def generate_profile(self, profile_name: str, *, scale: int = 1) -> dict[str, int]:
        profile = PROFILES[profile_name.lower()]
        self._ensure_paths(profile)
        self._ensure_season(profile_name)
        counts = {"paths": 0, "fields": 0, "quests": 0, "bursts": 0, "artifacts": 0, "resources": 0}

        paths = list(self.session.scalars(select(Path)))
        for path in paths:
            if path.name not in profile["paths"]:
                continue
            for field_name in profile["fields"]:
                field = Field(path_id=path.id, name=field_name, description=f"{field_name} field.", status="Active")
                self.session.add(field)
                self.session.flush()
                counts["fields"] += 1

                for quest_title in profile["quests"]:
                    quest = Quest(
                        field_id=field.id,
                        title=quest_title,
                        description=f"Quest for {field_name}.",
                        status=self.random.choice(["Active", "Active", "Paused", "Completed"]),
                        priority=self.random.choice(["Low", "Medium", "High"]),
                    )
                    self.session.add(quest)
                    self.session.flush()
                    counts["quests"] += 1

                    for burst_index in range(2 * scale):
                        burst = Burst(
                            quest_id=quest.id,
                            title=f"{quest_title} session {burst_index + 1}",
                            duration_minutes=self.random.choice([25, 45, 60, 90]),
                            notes="Focused work block.",
                            start_time=datetime.now() - timedelta(days=self.random.randint(0, 14)),
                        )
                        self.session.add(burst)
                        counts["bursts"] += 1

                    artifact = Artifact(
                        type=self.random.choice(profile["artifact_types"]),
                        title=f"{quest_title} insight",
                        content="Captured during active work.",
                    )
                    self.session.add(artifact)
                    self.session.flush()
                    counts["artifacts"] += 1
                    RelationshipService(self.session).auto_link_context(
                        entity_type="artifact",
                        entity_id=artifact.id,
                        path_id=path.id,
                        field_id=field.id,
                        quest_id=quest.id,
                    )

                    resource = Resource(
                        title=f"Reference for {quest_title}",
                        type=self.random.choice(profile["resources"]),
                        source="local-library",
                        progress=self.random.choice(["Not Started", "In Progress", "Reference"]),
                        notes="Useful reference material.",
                    )
                    self.session.add(resource)
                    counts["resources"] += 1

        for statement in profile["principles"]:
            self.session.add(Principle(statement=statement, description="Profile principle.", active=True))

        counts["paths"] = len([path for path in paths if path.name in profile["paths"]])
        self.session.flush()
        return counts

    def _ensure_paths(self, profile: dict[str, object]) -> None:
        existing = {path.name: path for path in self.session.scalars(select(Path))}
        icons = {"Builder": "B", "Warrior": "W", "Philosopher": "P", "Creator": "C", "Steward": "S", "Householder": "H"}
        for path_name in profile["paths"]:
            if path_name in existing:
                continue
            self.session.add(
                Path(
                    name=path_name,
                    description=f"{path_name} dimension.",
                    icon=icons.get(path_name, "•"),
                )
            )
        self.session.flush()

    def _ensure_season(self, profile_name: str) -> None:
        active = list(self.session.scalars(select(Season).where(Season.active.is_(True))))
        for season in active:
            season.active = False
        season = Season(
            name=f"{profile_name.title()} Season",
            description="Generated active season.",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=60),
            active=True,
        )
        self.session.add(season)
        self.session.flush()