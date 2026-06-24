from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def run_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    if "resources" in inspector.get_table_names():
        _ensure_timestamp_column(engine, "resources", "created_at")
    if "seasons" in inspector.get_table_names():
        _ensure_timestamp_column(engine, "seasons", "created_at")
    if "relationships" in inspector.get_table_names():
        _ensure_timestamp_column(engine, "relationships", "created_at")


def _ensure_timestamp_column(engine: Engine, table: str, column: str) -> None:
    """Add created_at to legacy tables.

    SQLite cannot ADD COLUMN with DEFAULT CURRENT_TIMESTAMP (non-constant default),
    so we add nullable, backfill, and rely on ORM server_default for new inserts.
    """
    inspector = inspect(engine)
    columns = {item["name"] for item in inspector.get_columns(table)}
    if column in columns:
        return
    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} DATETIME"))
        connection.execute(
            text(f"UPDATE {table} SET {column} = CURRENT_TIMESTAMP WHERE {column} IS NULL")
        )