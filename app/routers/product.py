from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_product_service, require_auth, require_manager
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.schemas.base import PaginatedResponse
from app.services.product import ProductService

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    dependencies=[Depends(require_auth)],
)


@router.post(
    "/",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    dependencies=[Depends(require_manager)],
)
async def create_product(
    body: ProductCreate,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    product = await service.create(body.model_dump())
    product = await service.get_by_id_with_category(product.id)
    return ProductRead.model_validate(product)


@router.get(
    "/",
    response_model=PaginatedResponse[ProductRead],
    summary="List all products",
)
async def list_products(
    category_id: int | None = None,
    offset: int = 0,
    limit: int = 100,
    service: ProductService = Depends(get_product_service),
) -> PaginatedResponse[ProductRead]:
    items, total = await service.get_all(
        offset=offset, limit=limit, category_id=category_id
    )
    return PaginatedResponse(
        items=[ProductRead.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Get a product by ID",
)
async def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    product = await service.get_by_id_with_category(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductRead.model_validate(product)


@router.patch(
    "/{product_id}",
    response_model=ProductRead,
    summary="Update a product",
    dependencies=[Depends(require_manager)],
)
async def update_product(
    product_id: int,
    body: ProductUpdate,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    product = await service.update(product_id, body.model_dump(exclude_unset=True))
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product = await service.get_by_id_with_category(product.id)
    return ProductRead.model_validate(product)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
    dependencies=[Depends(require_manager)],
)
async def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
) -> None:
    deleted = await service.delete(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
