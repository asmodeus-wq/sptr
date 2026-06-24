from __future__ import annotations

from sqlalchemy.orm import Session

from sparktrack_core.services.app_state import AppContext
from sparktrack_core.services.dev.fake_life_generator import FakeLifeGenerator
from sparktrack_core.services.dev.time_machine import TimeMachine


class ScreenshotMode:
    def __init__(self, session: Session) -> None:
        self.session = session

    def generate(self) -> AppContext:
        generator = FakeLifeGenerator(self.session)
        generator.clear_all()
        generator.generate_profile("builder", scale=3)
        TimeMachine(self.session).generate_history("2_years")

        from sqlalchemy import select

        from sparktrack_core.models import Field, Path, Quest, Season

        path = self.session.scalar(select(Path).where(Path.name == "Builder"))
        field = self.session.scalar(select(Field).where(Field.name == "SparkTrack"))
        quest = self.session.scalar(select(Quest).where(Quest.title == "Build SparkTrack Core"))
        season = self.session.scalar(select(Season).where(Season.active.is_(True)))

        return AppContext(
            path_id=path.id if path else None,
            field_id=field.id if field else None,
            quest_id=quest.id if quest else None,
            season_id=season.id if season else None,
        )