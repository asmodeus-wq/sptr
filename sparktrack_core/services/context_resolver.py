from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from sparktrack_core.models import Field, Path, Quest, Season
from sparktrack_core.services.app_state import AppContext


class ContextResolver:
    def __init__(self, session: Session) -> None:
        self.session = session

    def labels(self, context: AppContext) -> dict[str, str]:
        return {
            "path": self._path_name(context.path_id),
            "field": self._field_name(context.field_id),
            "quest": self._quest_title(context.quest_id),
            "season": self._season_name(context.season_id),
        }

    def resolve_quest_id(self, context: AppContext) -> int:
        if context.quest_id:
            quest = self.session.get(Quest, context.quest_id)
            if quest is not None:
                return quest.id

        if context.field_id:
            quest = self._first_active_quest_for_field(context.field_id)
            if quest is not None:
                return quest.id
            return self._ensure_inbox_quest(field_id=context.field_id)

        if context.path_id:
            field = self.session.scalar(
                select(Field).where(Field.path_id == context.path_id).order_by(Field.id).limit(1)
            )
            if field is None:
                field = Field(path_id=context.path_id, name="General", description="Default field.")
                self.session.add(field)
                self.session.flush()
            return self._ensure_inbox_quest(field_id=field.id)

        path = self.session.scalar(select(Path).order_by(Path.id).limit(1))
        if path is None:
            path = Path(name="Inbox", description="Default capture path.", icon="I")
            self.session.add(path)
            self.session.flush()

        field = self.session.scalar(select(Field).where(Field.path_id == path.id).limit(1))
        if field is None:
            field = Field(path_id=path.id, name="Capture", description="Quick capture field.")
            self.session.add(field)
            self.session.flush()

        return self._ensure_inbox_quest(field_id=field.id)

    def _ensure_inbox_quest(self, *, field_id: int) -> int:
        quest = self.session.scalar(
            select(Quest)
            .where(Quest.field_id == field_id, Quest.title == "Quick Capture")
            .limit(1)
        )
        if quest is not None:
            return quest.id

        quest = Quest(
            field_id=field_id,
            title="Quick Capture",
            description="Auto-created for context-aware capture.",
            status="Active",
            priority="Medium",
        )
        self.session.add(quest)
        self.session.flush()
        return quest.id

    def _first_active_quest_for_field(self, field_id: int) -> Quest | None:
        return self.session.scalar(
            select(Quest)
            .where(Quest.field_id == field_id, Quest.status == "Active")
            .order_by(Quest.id.desc())
            .limit(1)
        )

    def _path_name(self, path_id: int | None) -> str:
        if not path_id:
            return "No Path"
        path = self.session.get(Path, path_id)
        return path.name if path else "Unknown Path"

    def _field_name(self, field_id: int | None) -> str:
        if not field_id:
            return "No Field"
        field = self.session.get(Field, field_id)
        return field.name if field else "Unknown Field"

    def _quest_title(self, quest_id: int | None) -> str:
        if not quest_id:
            return "No Quest"
        quest = self.session.get(Quest, quest_id)
        return quest.title if quest else "Unknown Quest"

    def _season_name(self, season_id: int | None) -> str:
        if season_id:
            season = self.session.get(Season, season_id)
            if season:
                return season.name
        season = self.session.scalar(select(Season).where(Season.active.is_(True)).limit(1))
        return season.name if season else "No Season"