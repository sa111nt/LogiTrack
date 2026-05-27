"""Generic base service."""

import logging
from typing import Generic, TypeVar

from app.repositories.base import BaseRepository

ModelT = TypeVar("ModelT")

logger = logging.getLogger(__name__)


class BaseService(Generic[ModelT]):
    def __init__(self, repository: BaseRepository[ModelT]) -> None:
        self.repository = repository

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        return await self.repository.get_by_id(entity_id)

    async def get_all(
        self, offset: int = 0, limit: int = 100
    ) -> tuple[list[ModelT], int]:
        return await self.repository.get_all(offset=offset, limit=limit)

    async def create(self, data: dict) -> ModelT:
        return await self.repository.create(data)

    async def update(self, entity_id: int, data: dict) -> ModelT | None:
        return await self.repository.update(entity_id, data)

    async def delete(self, entity_id: int) -> bool:
        return await self.repository.delete(entity_id)
