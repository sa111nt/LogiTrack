from unittest.mock import AsyncMock, Mock

import pytest

from app.core.exceptions import InsufficientStockError, InvalidMovementError
from app.models.movement import MovementType
from app.models.warehouse import Stock
from app.schemas.stock import StockMovementCreate
from app.services.stock import StockService


@pytest.mark.asyncio
async def test_ensure_sufficient_stock_success():
    mock_repo = Mock()
    mock_repo.get_stock = AsyncMock(
        return_value=Stock(product_id=1, warehouse_id=1, quantity=100)
    )
    service = StockService(repository=mock_repo)

    stock = await service._ensure_sufficient_stock(
        product_id=1, warehouse_id=1, required_qty=50
    )
    assert stock.quantity == 100


@pytest.mark.asyncio
async def test_ensure_sufficient_stock_raises_error_if_none():
    mock_repo = Mock()
    mock_repo.get_stock = AsyncMock(return_value=None)
    service = StockService(repository=mock_repo)

    with pytest.raises(InsufficientStockError) as exc_info:
        await service._ensure_sufficient_stock(
            product_id=1, warehouse_id=1, required_qty=50
        )
    assert exc_info.value.requested == 50
    assert exc_info.value.available == 0


@pytest.mark.asyncio
async def test_ensure_sufficient_stock_raises_error_if_not_enough():
    mock_repo = Mock()
    mock_repo.get_stock = AsyncMock(
        return_value=Stock(product_id=1, warehouse_id=1, quantity=10)
    )
    service = StockService(repository=mock_repo)

    with pytest.raises(InsufficientStockError) as exc_info:
        await service._ensure_sufficient_stock(
            product_id=1, warehouse_id=1, required_qty=50
        )
    assert exc_info.value.requested == 50
    assert exc_info.value.available == 10


def _make(movement_type: MovementType, **kwargs: int | None) -> StockMovementCreate:
    return StockMovementCreate(
        movement_type=movement_type,
        product_id=1,
        quantity=10,
        **kwargs,
    )


def test_validate_in_valid():
    StockService._validate_warehouse_refs(
        _make(MovementType.incoming, to_warehouse_id=1)
    )


def test_validate_in_missing_to_warehouse():
    with pytest.raises(InvalidMovementError):
        StockService._validate_warehouse_refs(_make(MovementType.incoming))


def test_validate_in_unexpected_from_warehouse():
    with pytest.raises(InvalidMovementError):
        StockService._validate_warehouse_refs(
            _make(MovementType.incoming, to_warehouse_id=1, from_warehouse_id=2)
        )


def test_validate_out_valid():
    StockService._validate_warehouse_refs(
        _make(MovementType.outgoing, from_warehouse_id=1)
    )


def test_validate_out_missing_from_warehouse():
    with pytest.raises(InvalidMovementError):
        StockService._validate_warehouse_refs(_make(MovementType.outgoing))


def test_validate_out_unexpected_to_warehouse():
    with pytest.raises(InvalidMovementError):
        StockService._validate_warehouse_refs(
            _make(MovementType.outgoing, from_warehouse_id=1, to_warehouse_id=2)
        )


def test_validate_transfer_valid():
    StockService._validate_warehouse_refs(
        _make(MovementType.transfer, from_warehouse_id=1, to_warehouse_id=2)
    )


def test_validate_transfer_missing_from_warehouse():
    with pytest.raises(InvalidMovementError):
        StockService._validate_warehouse_refs(
            _make(MovementType.transfer, to_warehouse_id=2)
        )


def test_validate_transfer_missing_to_warehouse():
    with pytest.raises(InvalidMovementError):
        StockService._validate_warehouse_refs(
            _make(MovementType.transfer, from_warehouse_id=1)
        )


def test_validate_transfer_same_warehouse():
    with pytest.raises(InvalidMovementError):
        StockService._validate_warehouse_refs(
            _make(MovementType.transfer, from_warehouse_id=1, to_warehouse_id=1)
        )
