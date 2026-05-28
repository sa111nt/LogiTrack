import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movement import StockMovement
from app.models.warehouse import Stock

logger = logging.getLogger(__name__)


class StockRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # Stock queries
    async def get_stock(self, product_id: int, warehouse_id: int) -> Stock | None:
        stmt = select(Stock).where(
            Stock.product_id == product_id,
            Stock.warehouse_id == warehouse_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_stock(self, product_id: int, warehouse_id: int) -> Stock:
        stock = await self.get_stock(product_id, warehouse_id)
        if stock is None:
            stock = Stock(
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=0,
            )
            self.session.add(stock)
            await self.session.flush()
        return stock

    async def get_stock_by_warehouse(
        self, warehouse_id: int, offset: int = 0, limit: int = 100
    ) -> list[Stock]:
        stmt = (
            select(Stock)
            .where(Stock.warehouse_id == warehouse_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_stock_by_product(self, product_id: int) -> list[Stock]:
        stmt = select(Stock).where(Stock.product_id == product_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # Movement queries
    async def get_movements(
        self, offset: int = 0, limit: int = 100, movement_type: str | None = None
    ) -> list[StockMovement]:
        stmt = select(StockMovement)
        if movement_type:
            stmt = stmt.where(StockMovement.movement_type == movement_type)

        stmt = (
            stmt.order_by(StockMovement.created_at.desc()).offset(offset).limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_movement(self, data: dict) -> StockMovement:
        movement = StockMovement(**data)
        self.session.add(movement)
        await self.session.flush()
        await self.session.refresh(movement)
        logger.info(
            "Created StockMovement id=%s type=%s product_id=%s qty=%s",
            movement.id,
            movement.movement_type,
            movement.product_id,
            movement.quantity,
        )
        return movement
