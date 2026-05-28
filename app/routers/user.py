from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_user_service, require_admin
from app.core.security import hash_password
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.base import PaginatedResponse
from app.services.user import UserService

router = APIRouter(
    prefix="/users", tags=["Users"], dependencies=[Depends(require_admin)]
)


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(
    body: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    data = body.model_dump()
    data["hashed_password"] = hash_password(data.pop("password"))
    user = await service.create(data)
    return UserRead.model_validate(user)


@router.get(
    "/",
    response_model=PaginatedResponse[UserRead],
    summary="List all users",
)
async def list_users(
    offset: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service),
) -> PaginatedResponse[UserRead]:
    items, total = await service.get_all(offset=offset, limit=limit)
    return PaginatedResponse(
        items=[UserRead.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get a user by ID",
)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    user = await service.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update a user",
)
async def update_user(
    user_id: int,
    body: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    user = await service.update(user_id, body.model_dump(exclude_unset=True))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> None:
    deleted = await service.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
