from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_product_service
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "/",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
)
async def create_product(
    body: ProductCreate,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    product = await service.create(body.model_dump())
    return ProductRead.model_validate(product)


@router.get(
    "/",
    response_model=list[ProductRead],
    summary="List all products",
)
async def list_products(
    offset: int = 0,
    limit: int = 100,
    service: ProductService = Depends(get_product_service),
) -> list[ProductRead]:
    items, _ = await service.get_all(offset=offset, limit=limit)
    return [ProductRead.model_validate(item) for item in items]


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Get a product by ID",
)
async def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    product = await service.get_by_id(product_id)
    return ProductRead.model_validate(product)


@router.patch(
    "/{product_id}",
    response_model=ProductRead,
    summary="Update a product",
)
async def update_product(
    product_id: int,
    body: ProductUpdate,
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    product = await service.update(
        product_id, body.model_dump(exclude_unset=True)
    )
    return ProductRead.model_validate(product)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
)
async def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
) -> None:
    await service.delete(product_id)
