from __future__ import annotations

import random
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from sparktrack_core.models import Artifact, Burst, Quest, Resource
from sparktrack_core.services.dev.fake_life_generator import FakeLifeGenerator


HISTORY_WINDOWS = {
    "1_week": 7,
    "1_month": 30,
    "6_months": 182,
    "2_years": 730,
}


class TimeMachine:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.random = random.Random(99)

    def generate_history(self, window_key: str) -> dict[str, int]:
        days = HISTORY_WINDOWS[window_key]
        counts = {"bursts": 0, "artifacts": 0, "resources": 0}

        quests = list(self.session.scalars(select(Quest)))
        if not quests:
            FakeLifeGenerator(self.session).generate_profile("polymath", scale=1)
            quests = list(self.session.scalars(select(Quest)))

        now = datetime.now()
        for day_offset in range(days):
            if self.random.random() > 0.55:
                continue
            day = now - timedelta(days=day_offset)
            activity_count = self.random.randint(1, 4)
            for _ in range(activity_count):
                quest = self.random.choice(quests)
                stamp = day.replace(
                    hour=self.random.randint(6, 22),
                    minute=self.random.randint(0, 59),
                    second=0,
                    microsecond=0,
                )
                burst = Burst(
                    quest_id=quest.id,
                    title=f"Historical burst {day_offset}",
                    duration_minutes=self.random.choice([25, 45, 60]),
                    notes="Time-machine generated burst.",
                    start_time=stamp,
                    end_time=stamp + timedelta(minutes=25),
                )
                self.session.add(burst)
                counts["bursts"] += 1

                artifact = Artifact(
                    type=self.random.choice(["Idea", "Reflection", "Lesson", "Research Note"]),
                    title=f"Historical note {day_offset}-{self.random.randint(1, 99)}",
                    content="Generated historical artifact.",
                )
                artifact.created_at = stamp
                self.session.add(artifact)
                counts["artifacts"] += 1

                if self.random.random() > 0.7:
                    resource = Resource(
                        title=f"Historical resource {day_offset}",
                        type=self.random.choice(["Article", "Book", "Video"]),
                        source="archive",
                        progress="Reference",
                        notes="Generated historical resource.",
                    )
                    resource.created_at = stamp
                    self.session.add(resource)
                    counts["resources"] += 1

        self.session.flush()
        return counts