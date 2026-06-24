from __future__ import annotations

from datetime import datetime


def narrate_event(event: dict[str, object]) -> dict[str, object]:
    """Transform raw feed events into human-readable narrative cards."""
    entity_type = str(event.get("entity_type", ""))
    title = str(event.get("title", ""))
    quest = str(event.get("quest_title", ""))
    field = str(event.get("field_name", ""))
    path = str(event.get("path_name", ""))
    preview = str(event.get("preview", ""))[:100]

    templates = {
        "burst": _burst_line(title, quest, field, preview, event),
        "artifact": _artifact_line(title, quest, field, preview, event),
        "resource": _resource_line(title, preview, event),
        "quest": f"Started quest: {title}",
    }

    headline = templates.get(entity_type, f"Activity: {title}")
    context_line = _context_line(path, field, quest)
    timestamp = event.get("timestamp")

    return {
        **event,
        "headline": headline,
        "context_line": context_line,
        "time_ago": _time_ago(timestamp),
        "icon": _icon(entity_type),
        "health": _health_hint(entity_type, event),
    }


def _burst_line(title: str, quest: str, field: str, preview: str, event: dict) -> str:
    minutes = event.get("preview", "")
    if quest and quest != "—":
        if preview and "min" not in str(preview):
            return f"Worked on {quest}: {title}"
        return f"Focused on {quest} ({preview or 'session'})"
    return f"Completed burst: {title}"


def _artifact_line(title: str, quest: str, field: str, preview: str, event: dict) -> str:
    artifact_type = str(event.get("preview", ""))
    if "Reflection" in artifact_type or event.get("summary") == "Reflection":
        return f"Reflected on {field or quest or 'life'}: {title}"
    if quest and quest != "—":
        return f"Captured insight for {quest}: {title}"
    if field and field != "—":
        return f"Noted in {field}: {title}"
    return f"Captured: {title}"


def _resource_line(title: str, preview: str, _event: dict) -> str:
    return f"Added resource: {title}"


def _context_line(path: str, field: str, quest: str) -> str:
    parts = [p for p in (path, field, quest) if p and p != "—"]
    return " → ".join(parts) if parts else ""


def _time_ago(timestamp: object) -> str:
    if not isinstance(timestamp, datetime):
        return ""
    delta = datetime.now() - timestamp
    minutes = int(delta.total_seconds() / 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days}d ago"
    return timestamp.strftime("%b %d")


def _icon(entity_type: str) -> str:
    return {"burst": "⚡", "artifact": "💡", "resource": "📚", "quest": "🎯"}.get(entity_type, "·")


def _health_hint(entity_type: str, event: dict) -> str:
    if entity_type == "burst":
        return "progress"
    if entity_type == "artifact":
        return "insight"
    return "activity"