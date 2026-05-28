from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_category_service, require_auth, require_manager
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.base import PaginatedResponse
from app.services.category import CategoryService

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    dependencies=[Depends(require_auth)],
)


@router.post(
    "/",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    dependencies=[Depends(require_manager)],
)
async def create_category(
    body: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    category = await service.create(body.model_dump())
    return CategoryRead.model_validate(category)


@router.get(
    "/",
    response_model=PaginatedResponse[CategoryRead],
    summary="List all categories",
)
async def list_categories(
    offset: int = 0,
    limit: int = 100,
    service: CategoryService = Depends(get_category_service),
) -> PaginatedResponse[CategoryRead]:
    items, total = await service.get_all(offset=offset, limit=limit)
    return PaginatedResponse(
        items=[CategoryRead.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Get a category by ID",
)
async def get_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    category = await service.get_by_id(category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryRead.model_validate(category)


@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Update a category",
    dependencies=[Depends(require_manager)],
)
async def update_category(
    category_id: int,
    body: CategoryUpdate,
    service: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    category = await service.update(category_id, body.model_dump(exclude_unset=True))
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryRead.model_validate(category)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
    dependencies=[Depends(require_manager)],
)
async def delete_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
) -> None:
    deleted = await service.delete(category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
