from unittest.mock import AsyncMock, Mock

import pytest

from app.core.exceptions import InsufficientStockError
from app.models.warehouse import Stock
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
