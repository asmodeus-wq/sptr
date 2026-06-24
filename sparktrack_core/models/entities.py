from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sparktrack_core.database.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )


class Path(Base, TimestampMixin):
    __tablename__ = "paths"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    icon: Mapped[str] = mapped_column(String(48), default="", nullable=False)

    fields: Mapped[list["Field"]] = relationship(
        back_populates="path",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Path(id={self.id!r}, name={self.name!r})"


class Field(Base, TimestampMixin):
    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path_id: Mapped[int] = mapped_column(ForeignKey("paths.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(48), default="Active", nullable=False)

    path: Mapped[Path] = relationship(back_populates="fields")
    quests: Mapped[list["Quest"]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
    )


class Quest(Base, TimestampMixin):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(48), default="Active", nullable=False)
    priority: Mapped[str] = mapped_column(String(48), default="Medium", nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    field: Mapped[Field] = relationship(back_populates="quests")
    bursts: Mapped[list["Burst"]] = relationship(
        back_populates="quest",
        cascade="all, delete-orphan",
    )


class Burst(Base, TimestampMixin):
    __tablename__ = "bursts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    quest: Mapped[Quest] = relationship(back_populates="bursts")


class Artifact(Base, TimestampMixin):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)


class Resource(Base, TimestampMixin):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    source: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    progress: Mapped[str] = mapped_column(String(80), default="Not Started", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class Season(Base, TimestampMixin):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Principle(Base, TimestampMixin):
    __tablename__ = "principles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    statement: Mapped[str] = mapped_column(String(280), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Relationship(Base, TimestampMixin):
    __tablename__ = "relationships"
    __table_args__ = (
        Index("ix_relationships_source", "source_type", "source_id"),
        Index("ix_relationships_target", "target_type", "target_id"),
        Index(
            "ix_relationships_unique_edge",
            "source_type",
            "source_id",
            "target_type",
            "target_id",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)
