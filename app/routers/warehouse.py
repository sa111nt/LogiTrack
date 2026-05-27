from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_warehouse_service
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate
from app.services.warehouse import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


@router.post(
    "/",
    response_model=WarehouseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new warehouse",
)
async def create_warehouse(
    body: WarehouseCreate,
    service: WarehouseService = Depends(get_warehouse_service),
) -> WarehouseRead:
    warehouse = await service.create(body.model_dump())
    return WarehouseRead.model_validate(warehouse)


@router.get(
    "/",
    response_model=list[WarehouseRead],
    summary="List all warehouses",
)
async def list_warehouses(
    offset: int = 0,
    limit: int = 100,
    service: WarehouseService = Depends(get_warehouse_service),
) -> list[WarehouseRead]:
    items, _ = await service.get_all(offset=offset, limit=limit)
    return [WarehouseRead.model_validate(item) for item in items]


@router.get(
    "/{warehouse_id}",
    response_model=WarehouseRead,
    summary="Get a warehouse by ID",
)
async def get_warehouse(
    warehouse_id: int,
    service: WarehouseService = Depends(get_warehouse_service),
) -> WarehouseRead:
    warehouse = await service.get_by_id(warehouse_id)
    return WarehouseRead.model_validate(warehouse)


@router.patch(
    "/{warehouse_id}",
    response_model=WarehouseRead,
    summary="Update a warehouse",
)
async def update_warehouse(
    warehouse_id: int,
    body: WarehouseUpdate,
    service: WarehouseService = Depends(get_warehouse_service),
) -> WarehouseRead:
    warehouse = await service.update(
        warehouse_id, body.model_dump(exclude_unset=True)
    )
    return WarehouseRead.model_validate(warehouse)


@router.delete(
    "/{warehouse_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a warehouse",
)
async def delete_warehouse(
    warehouse_id: int,
    service: WarehouseService = Depends(get_warehouse_service),
) -> None:
    await service.delete(warehouse_id)
