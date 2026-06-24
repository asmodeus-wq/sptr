from collections.abc import Iterable
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class Repository(Generic[ModelT]):
    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def list(self, limit: int | None = None) -> list[ModelT]:
        statement = select(self.model).order_by(self.model.id.desc())
        if limit:
            statement = statement.limit(limit)
        return list(self.session.scalars(statement))

    def get(self, item_id: int) -> ModelT | None:
        return self.session.get(self.model, item_id)

    def create(self, values: dict[str, Any]) -> ModelT:
        item = self.model(**values)
        self.session.add(item)
        self.session.flush()
        return item

    def update(self, item_id: int, values: dict[str, Any]) -> ModelT | None:
        item = self.get(item_id)
        if item is None:
            return None
        for key, value in values.items():
            setattr(item, key, value)
        self.session.flush()
        return item

    def delete(self, item_id: int) -> bool:
        item = self.get(item_id)
        if item is None:
            return False
        self.session.delete(item)
        self.session.flush()
        return True

    def count(self) -> int:
        return len(list(self.session.scalars(select(self.model.id))))

    def bulk_create(self, rows: Iterable[dict[str, Any]]) -> None:
        for row in rows:
            self.session.add(self.model(**row))
        self.session.flush()
