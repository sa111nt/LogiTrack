from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.repositories.stock import StockRepository
from app.repositories.supplier import SupplierRepository
from app.repositories.warehouse import WarehouseRepository
from app.services.category import CategoryService
from app.services.product import ProductService
from app.services.stock import StockService
from app.services.supplier import SupplierService
from app.services.warehouse import WarehouseService


async def get_category_service(
    session: AsyncSession = Depends(get_async_db),
) -> AsyncGenerator[CategoryService, None]:
    repo = CategoryRepository(session)
    yield CategoryService(repo)


async def get_supplier_service(
    session: AsyncSession = Depends(get_async_db),
) -> AsyncGenerator[SupplierService, None]:
    repo = SupplierRepository(session)
    yield SupplierService(repo)


async def get_product_service(
    session: AsyncSession = Depends(get_async_db),
) -> AsyncGenerator[ProductService, None]:
    repo = ProductRepository(session)
    yield ProductService(repo)


async def get_warehouse_service(
    session: AsyncSession = Depends(get_async_db),
) -> AsyncGenerator[WarehouseService, None]:
    repo = WarehouseRepository(session)
    yield WarehouseService(repo)


async def get_stock_service(
    session: AsyncSession = Depends(get_async_db),
) -> AsyncGenerator[StockService, None]:
    repo = StockRepository(session)
    yield StockService(repo)
