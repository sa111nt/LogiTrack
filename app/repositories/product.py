from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Product, session)

    async def get_all(
        self, offset: int = 0, limit: int = 100, category_id: int | None = None
    ) -> tuple[list[Product], int]:
        stmt = select(Product).options(joinedload(Product.category))
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)

        # Count total items
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.session.scalar(count_stmt)

        # Fetch items
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total or 0

    async def get_by_sku(self, sku: str) -> Product | None:
        stmt = select(Product).where(Product.sku == sku)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_category(self, product_id: int) -> Product | None:
        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.id == product_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
