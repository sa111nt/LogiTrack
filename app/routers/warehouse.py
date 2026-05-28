from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_warehouse_service, require_auth, require_manager
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate
from app.schemas.base import PaginatedResponse
from app.services.warehouse import WarehouseService

router = APIRouter(
    prefix="/warehouses",
    tags=["Warehouses"],
    dependencies=[Depends(require_auth)],
)


@router.post(
    "/",
    response_model=WarehouseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new warehouse",
    dependencies=[Depends(require_manager)],
)
async def create_warehouse(
    body: WarehouseCreate,
    service: WarehouseService = Depends(get_warehouse_service),
) -> WarehouseRead:
    warehouse = await service.create(body.model_dump())
    return WarehouseRead.model_validate(warehouse)


@router.get(
    "/",
    response_model=PaginatedResponse[WarehouseRead],
    summary="List all warehouses",
)
async def list_warehouses(
    offset: int = 0,
    limit: int = 100,
    service: WarehouseService = Depends(get_warehouse_service),
) -> PaginatedResponse[WarehouseRead]:
    items, total = await service.get_all(offset=offset, limit=limit)
    return PaginatedResponse(
        items=[WarehouseRead.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


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
    if warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return WarehouseRead.model_validate(warehouse)


@router.patch(
    "/{warehouse_id}",
    response_model=WarehouseRead,
    summary="Update a warehouse",
    dependencies=[Depends(require_manager)],
)
async def update_warehouse(
    warehouse_id: int,
    body: WarehouseUpdate,
    service: WarehouseService = Depends(get_warehouse_service),
) -> WarehouseRead:
    warehouse = await service.update(warehouse_id, body.model_dump(exclude_unset=True))
    if warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return WarehouseRead.model_validate(warehouse)


@router.delete(
    "/{warehouse_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a warehouse",
    dependencies=[Depends(require_manager)],
)
async def delete_warehouse(
    warehouse_id: int,
    service: WarehouseService = Depends(get_warehouse_service),
) -> None:
    deleted = await service.delete(warehouse_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Warehouse not found")
