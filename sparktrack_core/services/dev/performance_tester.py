from __future__ import annotations

import random
import time
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Field, Path, Quest
from sparktrack_core.services.dashboard_service import DashboardService
from sparktrack_core.services.relationship_service import RelationshipService
from sparktrack_core.services.search_service import SearchService
from sparktrack_core.services.app_state import AppContext


class PerformanceTester:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.random = random.Random(7)

    def generate_records(self, count: int) -> int:
        path = self.session.scalar(select(Path).limit(1))
        if path is None:
            path = Path(name="Perf Path", description="Performance path.", icon="P")
            self.session.add(path)
            self.session.flush()

        field = self.session.scalar(select(Field).where(Field.path_id == path.id).limit(1))
        if field is None:
            field = Field(path_id=path.id, name="Perf Field", description="Performance field.")
            self.session.add(field)
            self.session.flush()

        quest = self.session.scalar(select(Quest).where(Quest.field_id == field.id).limit(1))
        if quest is None:
            quest = Quest(field_id=field.id, title="Perf Quest", description="Performance quest.")
            self.session.add(quest)
            self.session.flush()

        created = 0
        for index in range(count):
            if index % 3 == 0:
                row = Burst(
                    quest_id=quest.id,
                    title=f"Perf burst {index}",
                    duration_minutes=25,
                    notes="performance",
                    start_time=datetime.now() - timedelta(minutes=index),
                )
            elif index % 3 == 1:
                row = Artifact(type="Idea", title=f"Perf artifact {index}", content="performance")
                self.session.add(row)
                self.session.flush()
                RelationshipService(self.session).link("artifact", row.id, "quest", quest.id)
                created += 1
                continue
            else:
                row = Artifact(type="Research Note", title=f"Perf note {index}", content="performance")
            self.session.add(row)
            created += 1
        self.session.flush()
        return created

    def benchmark(self) -> dict[str, float]:
        context = AppContext()

        start = time.perf_counter()
        DashboardService(self.session).snapshot(context)
        dashboard_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        SearchService(self.session).search("perf", limit=50)
        search_ms = (time.perf_counter() - start) * 1000

        artifact = self.session.scalar(select(Artifact).limit(1))
        start = time.perf_counter()
        if artifact is not None:
            RelationshipService(self.session).list_for_entity("artifact", artifact.id)
        relationship_ms = (time.perf_counter() - start) * 1000

        return {
            "dashboard_load_ms": round(dashboard_ms, 2),
            "search_ms": round(search_ms, 2),
            "relationship_query_ms": round(relationship_ms, 2),
        }