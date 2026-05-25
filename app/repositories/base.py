"""Generic async base repository."""

import logging
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)

logger = logging.getLogger(__name__)


class BaseRepository(Generic[ModelT]):
    """Async CRUD repository with pagination."""

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        stmt = select(self.model).where(self.model.id == entity_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[ModelT], int]:
        """
        Returns (items, total_count) for paginated responses.
        """
        count_stmt = select(func.count()).select_from(self.model)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def create(self, data: dict) -> ModelT:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        logger.info("Created %s id=%s", self.model.__tablename__, instance.id)
        return instance

    async def update(self, entity_id: int, data: dict) -> ModelT | None:
        instance = await self.get_by_id(entity_id)
        if instance is None:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        logger.info("Updated %s id=%s", self.model.__tablename__, entity_id)
        return instance

    async def delete(self, entity_id: int) -> bool:
        instance = await self.get_by_id(entity_id)
        if instance is None:
            return False

        await self.session.delete(instance)
        await self.session.flush()
        logger.info("Deleted %s id=%s", self.model.__tablename__, entity_id)
        return True
