from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_supplier_service, require_auth, require_manager
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from app.schemas.base import PaginatedResponse
from app.services.supplier import SupplierService

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
    dependencies=[Depends(require_auth)],
)


@router.post(
    "/",
    response_model=SupplierRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new supplier",
    dependencies=[Depends(require_manager)],
)
async def create_supplier(
    body: SupplierCreate,
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierRead:
    supplier = await service.create(body.model_dump())
    return SupplierRead.model_validate(supplier)


@router.get(
    "/",
    response_model=PaginatedResponse[SupplierRead],
    summary="List all suppliers",
)
async def list_suppliers(
    offset: int = 0,
    limit: int = 100,
    service: SupplierService = Depends(get_supplier_service),
) -> PaginatedResponse[SupplierRead]:
    items, total = await service.get_all(offset=offset, limit=limit)
    return PaginatedResponse(
        items=[SupplierRead.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{supplier_id}",
    response_model=SupplierRead,
    summary="Get a supplier by ID",
)
async def get_supplier(
    supplier_id: int,
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierRead:
    supplier = await service.get_by_id(supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SupplierRead.model_validate(supplier)


@router.patch(
    "/{supplier_id}",
    response_model=SupplierRead,
    summary="Update a supplier",
    dependencies=[Depends(require_manager)],
)
async def update_supplier(
    supplier_id: int,
    body: SupplierUpdate,
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierRead:
    supplier = await service.update(supplier_id, body.model_dump(exclude_unset=True))
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SupplierRead.model_validate(supplier)


@router.delete(
    "/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a supplier",
    dependencies=[Depends(require_manager)],
)
async def delete_supplier(
    supplier_id: int,
    service: SupplierService = Depends(get_supplier_service),
) -> None:
    deleted = await service.delete(supplier_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Supplier not found")
