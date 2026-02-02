from __future__ import annotations

from typing import Any, Generic, Mapping, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    model: Type[ModelType] | None = None

    def __init__(self, db: Session) -> None:
        self._db = db

    @property
    def db(self) -> Session:
        return self._db

    def _model(self) -> Type[ModelType]:
        if self.model is None:
            raise RuntimeError("Repository model is not set.")
        return self.model

    def get_by_pk(self, *pk_values: Any) -> ModelType | None:
        key = pk_values[0] if len(pk_values) == 1 else tuple(pk_values)
        return self._db.get(self._model(), key)

    def get_one(self, **filters: Any) -> ModelType | None:
        stmt = select(self._model()).filter_by(**filters)
        return self._db.execute(stmt).scalars().first()

    def get_many(
        self,
        *,
        offset: int = 0,
        limit: int | None = 100,
        **filters: Any,
    ) -> list[ModelType]:
        stmt = select(self._model()).filter_by(**filters).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self._db.execute(stmt).scalars().all())

    def exists(self, **filters: Any) -> bool:
        stmt = select(func.count()).select_from(self._model()).filter_by(**filters)
        return (self._db.execute(stmt).scalar_one() or 0) > 0

    def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self._model()).filter_by(**filters)
        return int(self._db.execute(stmt).scalar_one() or 0)

    def create(self, obj_in: Mapping[str, Any], *, commit: bool = True) -> ModelType:
        model = self._model()
        obj = model(**dict(obj_in))
        self._db.add(obj)
        if commit:
            self._db.commit()
            self._db.refresh(obj)
        else:
            self._db.flush()
        return obj

    def update(
        self,
        db_obj: ModelType,
        obj_in: Mapping[str, Any],
        *,
        commit: bool = True,
    ) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        if commit:
            self._db.commit()
            self._db.refresh(db_obj)
        else:
            self._db.flush()
        return db_obj

    def delete(self, db_obj: ModelType, *, commit: bool = True) -> None:
        self._db.delete(db_obj)
        if commit:
            self._db.commit()
        else:
            self._db.flush()
