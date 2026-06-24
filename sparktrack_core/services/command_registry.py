from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandItem:
    id: str
    label: str
    keywords: str
    category: str
    handler_key: str
    payload: str = ""
    ai_ready: bool = False


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: list[CommandItem] = [
            CommandItem("open_now", "Go to Now", "home now current", "Navigate", "nav_now"),
            CommandItem("quick_capture", "Quick Capture", "capture idea burst", "Capture", "quick_capture"),
            CommandItem("create_burst", "Create Burst", "burst focus session", "Create", "capture_burst"),
            CommandItem("create_artifact", "Create Artifact", "artifact note output", "Create", "capture_artifact"),
            CommandItem("create_reflection", "Create Reflection", "reflection journal", "Create", "capture_reflection"),
            CommandItem("create_resource", "Create Resource", "resource book", "Create", "capture_resource"),
            CommandItem("open_settings", "Open Settings", "preferences", "Navigate", "nav_settings"),
            CommandItem("data_explorer", "Open Data Explorer", "smart views tables", "Data", "nav_smart_views"),
            CommandItem("open_quests_data", "Quests Table", "data quests raw", "Data", "nav_quests"),
            CommandItem("open_artifacts_data", "Artifacts Table", "data artifacts raw", "Data", "nav_artifacts"),
            CommandItem("open_bursts_data", "Bursts Table", "data bursts raw", "Data", "nav_bursts"),
            CommandItem("open_paths_data", "Paths Table", "data paths infrastructure", "Data", "nav_paths"),
            CommandItem("open_fields_data", "Fields Table", "data fields infrastructure", "Data", "nav_fields"),
            CommandItem("open_resources_data", "Resources Table", "data resources", "Data", "nav_resources"),
            CommandItem("open_principles_data", "Principles Table", "data principles", "Data", "nav_principles"),
            CommandItem("open_dashboard", "Dashboard (Legacy)", "stats overview", "Data", "nav_dashboard"),
            CommandItem("set_context", "Set Context", "path field quest season", "Context", "set_context"),
            CommandItem(
                "ai_analyze_future",
                "AI Analyze (Future)",
                "ai llm analyze",
                "AI",
                "ai_placeholder",
                ai_ready=True,
            ),
        ]
        self._workspace_commands: list[CommandItem] = []

    def set_workspace_commands(self, commands: list[CommandItem]) -> None:
        self._workspace_commands = commands

    def all_commands(self) -> list[CommandItem]:
        return [*self._commands, *self._workspace_commands]

    def filter(self, query: str) -> list[CommandItem]:
        needle = query.strip().lower()
        if not needle:
            return self.all_commands()[:20]

        scored: list[tuple[int, CommandItem]] = []
        for command in self.all_commands():
            haystack = f"{command.label} {command.keywords} {command.category}".lower()
            if needle in command.label.lower():
                scored.append((100, command))
            elif needle in haystack:
                scored.append((60, command))
            elif any(part in haystack for part in needle.split()):
                scored.append((40, command))

        scored.sort(key=lambda item: (-item[0], item[1].label))
        return [command for _, command in scored[:20]]