from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QSettings, Signal


@dataclass
class AppContext:
    path_id: int | None = None
    field_id: int | None = None
    quest_id: int | None = None
    season_id: int | None = None

    def as_dict(self) -> dict[str, int | None]:
        return {
            "path_id": self.path_id,
            "field_id": self.field_id,
            "quest_id": self.quest_id,
            "season_id": self.season_id,
        }


class AppStateService(QObject):
    context_changed = Signal()
    workspace_changed = Signal()
    developer_mode_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("SparkTrack", "SparkTrack Core")
        self._context = self._load_context()
        self._workspace_id = str(self._settings.value("workspace_id", "all") or "all")
        self._developer_mode = self._settings.value("developer_mode", False, type=bool)
        self._favorites: list[str] = list(self._settings.value("sidebar_favorites", []) or [])
        self._pinned: list[str] = list(self._settings.value("sidebar_pinned", []) or [])
        self._pinned_workspaces: list[str] = list(self._settings.value("pinned_workspaces", []) or [])
        self._recent_quests: list[int] = self._load_int_list("recent_quests")

    @property
    def context(self) -> AppContext:
        return self._context

    @property
    def workspace_id(self) -> str:
        return self._workspace_id

    @property
    def developer_mode(self) -> bool:
        return self._developer_mode

    @property
    def favorites(self) -> list[str]:
        return list(self._favorites)

    @property
    def pinned(self) -> list[str]:
        return list(self._pinned)

    @property
    def pinned_workspaces(self) -> list[str]:
        return list(self._pinned_workspaces)

    @property
    def recent_quests(self) -> list[int]:
        return list(self._recent_quests)

    def set_context(
        self,
        *,
        path_id: int | None = None,
        field_id: int | None = None,
        quest_id: int | None = None,
        season_id: int | None = None,
        clear_missing: bool = False,
    ) -> None:
        if clear_missing:
            self._context = AppContext(path_id, field_id, quest_id, season_id)
        else:
            current = self._context
            self._context = AppContext(
                path_id if path_id is not None else current.path_id,
                field_id if field_id is not None else current.field_id,
                quest_id if quest_id is not None else current.quest_id,
                season_id if season_id is not None else current.season_id,
            )
        self._persist_context()
        self.context_changed.emit()

    def set_workspace(self, workspace_id: str) -> None:
        workspace_id = workspace_id or "all"
        if workspace_id == self._workspace_id:
            return
        self._workspace_id = workspace_id
        self._settings.setValue("workspace_id", self._workspace_id)
        self.workspace_changed.emit()

    def set_developer_mode(self, enabled: bool) -> None:
        self._developer_mode = enabled
        self._settings.setValue("developer_mode", enabled)
        self.developer_mode_changed.emit(enabled)

    def set_favorites(self, items: list[str]) -> None:
        self._favorites = items
        self._settings.setValue("sidebar_favorites", items)

    def set_pinned(self, items: list[str]) -> None:
        self._pinned = items
        self._settings.setValue("sidebar_pinned", items)

    def set_pinned_workspaces(self, items: list[str]) -> None:
        self._pinned_workspaces = items
        self._settings.setValue("pinned_workspaces", items)

    def push_recent_quest(self, quest_id: int) -> None:
        items = [quest_id] + [q for q in self._recent_quests if q != quest_id]
        self._recent_quests = items[:8]
        self._settings.setValue("recent_quests", self._recent_quests)

    def save_window_state(self, geometry: bytes, state: bytes, page_index: int) -> None:
        self._settings.setValue("window_geometry", geometry)
        self._settings.setValue("window_state", state)
        self._settings.setValue("active_page", page_index)

    def restore_window_geometry(self) -> bytes | None:
        value = self._settings.value("window_geometry")
        return value if isinstance(value, (bytes, bytearray)) else None

    def restore_window_state(self) -> bytes | None:
        value = self._settings.value("window_state")
        return value if isinstance(value, (bytes, bytearray)) else None

    def restore_active_page(self) -> int:
        return int(self._settings.value("active_page", 0))

    def _load_context(self) -> AppContext:
        return AppContext(
            path_id=self._int_or_none("context_path_id"),
            field_id=self._int_or_none("context_field_id"),
            quest_id=self._int_or_none("context_quest_id"),
            season_id=self._int_or_none("context_season_id"),
        )

    def _persist_context(self) -> None:
        for key, value in self._context.as_dict().items():
            self._settings.setValue(f"context_{key}", value if value is not None else "")

    def _load_int_list(self, key: str) -> list[int]:
        raw = self._settings.value(key, [])
        if not raw:
            return []
        return [int(item) for item in raw if str(item).isdigit()]

    def _int_or_none(self, key: str) -> int | None:
        raw = self._settings.value(key, "")
        if raw in ("", None):
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None