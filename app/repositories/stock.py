import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidMovementError
from app.models.movement import MovementType, StockMovement
from app.models.warehouse import Stock
from app.schemas.stock import StockMovementCreate

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
        self, offset: int = 0, limit: int = 100
    ) -> list[StockMovement]:
        stmt = (
            select(StockMovement)
            .order_by(StockMovement.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # Core transactional logic
    async def process_movement(
        self,
        data: StockMovementCreate,
        performed_by_id: int,
    ) -> StockMovement:
        """
        Execute a stock movement and update inventory levels.
        """
        self._validate_warehouse_refs(data)

        match data.movement_type:
            case MovementType.incoming:
                await self._process_incoming(data)
            case MovementType.outgoing:
                await self._process_outgoing(data)
            case MovementType.transfer:
                await self._process_transfer(data)

        movement = StockMovement(
            movement_type=data.movement_type,
            product_id=data.product_id,
            from_warehouse_id=data.from_warehouse_id,
            to_warehouse_id=data.to_warehouse_id,
            quantity=data.quantity,
            notes=data.notes,
            performed_by_id=performed_by_id,
        )
        self.session.add(movement)
        await self.session.flush()
        await self.session.refresh(movement)

        logger.info(
            "Processed %s movement id=%s: product=%s qty=%s",
            data.movement_type.value,
            movement.id,
            data.product_id,
            data.quantity,
        )
        return movement

    # Internal helpers
    @staticmethod
    def _validate_warehouse_refs(data: StockMovementCreate) -> None:
        match data.movement_type:
            case MovementType.incoming:
                if data.to_warehouse_id is None:
                    raise InvalidMovementError("IN movement requires to_warehouse_id")
                if data.from_warehouse_id is not None:
                    raise InvalidMovementError(
                        "IN movement must not have from_warehouse_id"
                    )
            case MovementType.outgoing:
                if data.from_warehouse_id is None:
                    raise InvalidMovementError(
                        "OUT movement requires from_warehouse_id"
                    )
                if data.to_warehouse_id is not None:
                    raise InvalidMovementError(
                        "OUT movement must not have to_warehouse_id"
                    )
            case MovementType.transfer:
                if data.from_warehouse_id is None or data.to_warehouse_id is None:
                    raise InvalidMovementError(
                        "TRANSFER movement requires both "
                        "from_warehouse_id and to_warehouse_id"
                    )
                if data.from_warehouse_id == data.to_warehouse_id:
                    raise InvalidMovementError(
                        "TRANSFER: from_warehouse and to_warehouse " "must be different"
                    )

    async def _get_or_create_stock(self, product_id: int, warehouse_id: int) -> Stock:
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

    async def _process_incoming(self, data: StockMovementCreate) -> None:
        assert data.to_warehouse_id is not None
        stock = await self._get_or_create_stock(data.product_id, data.to_warehouse_id)
        stock.quantity += data.quantity

    async def _process_outgoing(self, data: StockMovementCreate) -> None:
        assert data.from_warehouse_id is not None
        stock = await self._get_or_create_stock(data.product_id, data.to_warehouse_id)
        stock.quantity -= data.quantity

    async def _process_transfer(self, data: StockMovementCreate) -> None:
        assert data.from_warehouse_id is not None
        assert data.to_warehouse_id is not None

        source = await self._get_or_create_stock(data.product_id, data.to_warehouse_id)
        source.quantity -= data.quantity

        dest = await self._get_or_create_stock(data.product_id, data.to_warehouse_id)
        dest.quantity += data.quantity
