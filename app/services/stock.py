import json
import logging

import hashlib
from fastapi.encoders import jsonable_encoder

from app.core.exceptions import InsufficientStockError, InvalidMovementError, ResourceConflictError
from app.models.idempotency import IdempotencyKey
from app.models.movement import MovementType, StockMovement
from app.models.warehouse import Stock
from app.repositories.stock import StockRepository
from app.schemas.stock import StockMovementCreate, StockMovementRead

logger = logging.getLogger(__name__)


class StockService:
    def __init__(self, repository: StockRepository) -> None:
        self.repository = repository

    # Read operations
    async def get_stock_by_warehouse(
        self, warehouse_id: int, offset: int = 0, limit: int = 100
    ) -> list[Stock]:
        return await self.repository.get_stock_by_warehouse(warehouse_id, offset, limit)

    async def get_stock_by_product(self, product_id: int) -> list[Stock]:
        return await self.repository.get_stock_by_product(product_id)

    async def get_movements(
        self, offset: int = 0, limit: int = 100, movement_type: str | None = None
    ) -> list[StockMovement]:
        return await self.repository.get_movements(offset, limit, movement_type)

    # Core business operation
    async def process_movement(
        self,
        data: StockMovementCreate,
        performed_by_id: int,
        idempotency_key: str | None = None,
    ) -> StockMovementRead:
        # Idempotency check
        request_hash = ""
        if idempotency_key:
            session = self.repository.session
            cached = await session.get(IdempotencyKey, idempotency_key)
            # Create a deterministic fingerprint of the request
            request_hash = hashlib.sha256(
                json.dumps(data.model_dump(mode="json"), sort_keys=True).encode()
            ).hexdigest()
            if cached:
                if cached.user_id != performed_by_id:
                    raise ResourceConflictError(
                        "Idempotency key already used by a different user"
                    )
                if cached.request_hash != request_hash:
                    raise ResourceConflictError(
                        "Idempotency key already used for a different request"
                    )
                logger.info(f"Idempotency cache hit for {idempotency_key}")
                return StockMovementRead(**cached.response_body)

        self._validate_warehouse_refs(data)

        match data.movement_type:
            case MovementType.incoming:
                await self._process_incoming(data)
            case MovementType.outgoing:
                await self._process_outgoing(data)
            case MovementType.transfer:
                await self._process_transfer(data)

        movement = await self.repository.create_movement(
            {
                "movement_type": data.movement_type,
                "product_id": data.product_id,
                "from_warehouse_id": data.from_warehouse_id,
                "to_warehouse_id": data.to_warehouse_id,
                "quantity": data.quantity,
                "notes": data.notes,
                "performed_by_id": performed_by_id,
            }
        )

        logger.info(
            "Processed %s movement id=%s: product=%s qty=%s",
            data.movement_type.value,
            movement.id,
            data.product_id,
            data.quantity,
        )

        # Serialize for response and cache
        response_data = jsonable_encoder(StockMovementRead.model_validate(movement))

        if idempotency_key:
            session = self.repository.session
            idem = IdempotencyKey(
                key=idempotency_key,
                request_hash=request_hash,
                user_id=performed_by_id,
                status_code=201,
                response_body=response_data,
            )
            session.add(idem)
            await session.commit()

        return StockMovementRead.model_validate(movement)

    # Validation
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
                        "TRANSFER requires both from_warehouse_id "
                        "and to_warehouse_id"
                    )
                if data.from_warehouse_id == data.to_warehouse_id:
                    raise InvalidMovementError(
                        "TRANSFER: source and destination warehouses "
                        "must be different"
                    )

    # Stock validation
    async def _ensure_sufficient_stock(
        self, product_id: int, warehouse_id: int, required_qty: int
    ) -> Stock:
        stock = await self.repository.get_stock(
            product_id, warehouse_id, with_for_update=True
        )
        available = stock.quantity if stock else 0
        if available < required_qty:
            raise InsufficientStockError(
                product_id=product_id,
                warehouse_id=warehouse_id,
                requested=required_qty,
                available=available,
            )
        return stock  # type: ignore[return-value]

    # Movement processors
    async def _process_incoming(self, data: StockMovementCreate) -> None:
        assert data.to_warehouse_id is not None
        stock = await self.repository.get_or_create_stock(
            data.product_id, data.to_warehouse_id
        )
        stock.quantity += data.quantity

    async def _process_outgoing(self, data: StockMovementCreate) -> None:
        assert data.from_warehouse_id is not None
        stock = await self._ensure_sufficient_stock(
            data.product_id, data.from_warehouse_id, data.quantity
        )
        stock.quantity -= data.quantity

    async def _process_transfer(self, data: StockMovementCreate) -> None:
        assert data.from_warehouse_id is not None
        assert data.to_warehouse_id is not None

        source = await self._ensure_sufficient_stock(
            data.product_id, data.from_warehouse_id, data.quantity
        )
        source.quantity -= data.quantity

        dest = await self.repository.get_or_create_stock(
            data.product_id, data.to_warehouse_id
        )
        dest.quantity += data.quantity
