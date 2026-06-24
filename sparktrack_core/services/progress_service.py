from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sparktrack_core.models import Burst, Quest
from sparktrack_core.services.momentum_service import MomentumService
from sparktrack_core.services.workspace_service import WorkspaceScope, WorkspaceService


class ProgressService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.workspaces = WorkspaceService(session)

    def heatmap(self, scope: WorkspaceScope, *, days: int = 14) -> list[dict[str, object]]:
        """Daily activity intensity for heatmap visualization."""
        today = date.today()
        counts: dict[date, int] = {today - timedelta(days=i): 0 for i in range(days)}

        for burst in self.session.scalars(select(Burst).order_by(Burst.id.desc()).limit(500)):
            quest = self.session.get(Quest, burst.quest_id)
            if quest is None:
                continue
            from sparktrack_core.models import Field, Path

            field = self.session.get(Field, quest.field_id)
            path = self.session.get(Path, field.path_id) if field else None
            if field is None or path is None:
                continue
            if not self.workspaces.quest_belongs(field.id, path.id, scope):
                continue
            ts = burst.start_time or burst.created_at
            if ts and ts.date() in counts:
                counts[ts.date()] += 1

        max_count = max(counts.values()) or 1
        rows = []
        for day_offset in range(days - 1, -1, -1):
            day = today - timedelta(days=day_offset)
            count = counts[day]
            intensity = count / max_count
            rows.append({
                "date": day,
                "count": count,
                "intensity": intensity,
                "label": day.strftime("%a"),
            })
        return rows

    def quest_health(self, scope: WorkspaceScope) -> list[dict[str, object]]:
        momentum = MomentumService(self.session)
        rows = []
        for item in momentum.quest_momentum(scope):
            score = int(item["score"])
            rows.append({
                "id": item["id"],
                "title": item["title"],
                "bar": item["bar"],
                "status": item["status_label"],
                "health": self._health_label(score),
                "health_color": self._health_color(score),
            })
        return rows

    def consistency(self, scope: WorkspaceScope) -> dict[str, object]:
        heatmap = self.heatmap(scope, days=7)
        active_days = sum(1 for day in heatmap if day["count"] > 0)
        total_bursts = sum(day["count"] for day in heatmap)
        return {
            "active_days": active_days,
            "total_days": 7,
            "total_bursts": total_bursts,
            "streak_label": f"{active_days}/7 active days",
            "consistency_pct": int(active_days / 7 * 100),
        }

    def upcoming_decisions(self, scope: WorkspaceScope) -> list[dict[str, object]]:
        from sparktrack_core.models import Field, Path

        rows = []
        cutoff = date.today() + timedelta(days=14)
        for quest in self.session.scalars(select(Quest).where(Quest.status == "Active")):
            if quest.target_date is None or quest.target_date > cutoff:
                continue
            field = self.session.get(Field, quest.field_id)
            path = self.session.get(Path, field.path_id) if field else None
            if field is None or path is None:
                continue
            if not self.workspaces.quest_belongs(field.id, path.id, scope):
                continue
            days_left = (quest.target_date - date.today()).days
            rows.append({
                "id": quest.id,
                "title": quest.title,
                "target_date": quest.target_date,
                "days_left": days_left,
                "urgency": "soon" if days_left <= 3 else "upcoming",
            })
        rows.sort(key=lambda row: row["days_left"])
        return rows

    def _health_label(self, score: int) -> str:
        if score >= 8:
            return "Thriving"
        if score >= 3:
            return "Healthy"
        if score >= 1:
            return "Cooling"
        return "Dormant"

    def _health_color(self, score: int) -> str:
        if score >= 8:
            return "#4ADE80"
        if score >= 3:
            return "#5EA1FF"
        if score >= 1:
            return "#FBBF24"
        return "#6B7280"