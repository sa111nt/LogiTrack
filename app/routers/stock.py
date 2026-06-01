from fastapi import APIRouter, Depends, status, Header

from app.api.dependencies import get_current_user, get_stock_service, require_auth
from app.models.movement import MovementType
from app.models.user import User
from app.schemas.stock import StockMovementCreate, StockMovementRead, StockRead
from app.services.stock import StockService

router = APIRouter(
    prefix="/stock",
    tags=["Stock & Movements"],
    dependencies=[Depends(require_auth)],
)


@router.post(
    "/movements",
    response_model=StockMovementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Process a stock movement (IN / OUT / TRANSFER)",
)
async def create_movement(
    body: StockMovementCreate,
    current_user: User = Depends(get_current_user),
    service: StockService = Depends(get_stock_service),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> StockMovementRead:
    movement = await service.process_movement(
        body, current_user.id, idempotency_key=idempotency_key
    )
    return StockMovementRead.model_validate(movement)


@router.get(
    "/movements",
    response_model=list[StockMovementRead],
    summary="List stock movement history",
)
async def list_movements(
    movement_type: MovementType | None = None,
    offset: int = 0,
    limit: int = 100,
    service: StockService = Depends(get_stock_service),
) -> list[StockMovementRead]:
    items = await service.get_movements(
        offset=offset, limit=limit, movement_type=movement_type
    )
    return [StockMovementRead.model_validate(item) for item in items]


@router.get(
    "/warehouse/{warehouse_id}",
    response_model=list[StockRead],
    summary="Current inventory at a specific warehouse",
)
async def get_stock_by_warehouse(
    warehouse_id: int,
    offset: int = 0,
    limit: int = 100,
    service: StockService = Depends(get_stock_service),
) -> list[StockRead]:
    items = await service.get_stock_by_warehouse(
        warehouse_id, offset=offset, limit=limit
    )
    return [StockRead.model_validate(item) for item in items]


@router.get(
    "/product/{product_id}",
    response_model=list[StockRead],
    summary="Stock levels for a product across all warehouses",
)
async def get_stock_by_product(
    product_id: int,
    service: StockService = Depends(get_stock_service),
) -> list[StockRead]:
    items = await service.get_stock_by_product(product_id)
    return [StockRead.model_validate(item) for item in items]
