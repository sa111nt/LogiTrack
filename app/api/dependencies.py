from collections.abc import AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.models.revoked_token import RevokedToken
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.repositories.stock import StockRepository
from app.repositories.supplier import SupplierRepository
from app.repositories.user import UserRepository
from app.repositories.warehouse import WarehouseRepository
from app.services.auth import AuthService
from app.services.category import CategoryService
from app.services.product import ProductService
from app.services.stock import StockService
from app.services.supplier import SupplierService
from app.services.user import UserService
from app.services.warehouse import WarehouseService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token, expected_type="access")
        email: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")
        if email is None or jti is None:
            raise credentials_exception
            
        # Check if token is revoked
        revoked = await session.get(RevokedToken, jti)
        if revoked:
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.InvalidTokenError:
        raise credentials_exception from None

    repo = UserRepository(session)
    user = await repo.get_by_email(email)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return user


class RoleChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted",
            )
        return user


require_admin = RoleChecker([UserRole.admin])
require_manager = RoleChecker([UserRole.admin, UserRole.warehouse_manager])
require_auth = get_current_user


async def get_auth_service(
    session: AsyncSession = Depends(get_async_db),
) -> AsyncGenerator[AuthService, None]:
    repo = UserRepository(session)
    yield AuthService(repo, session)


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


async def get_user_service(
    session: AsyncSession = Depends(get_async_db),
) -> AsyncGenerator[UserService, None]:
    repo = UserRepository(session)
    yield UserService(repo)
