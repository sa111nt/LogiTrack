import logging

import jwt
from fastapi import HTTPException, status

from app.core.exceptions import AlreadyExistsError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import TokenPair
from app.schemas.user import UserRegister

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repo = user_repository

    async def register(self, data: UserRegister) -> User:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise AlreadyExistsError("User", "email", data.email)

        user_data = data.model_dump()
        user_data["hashed_password"] = hash_password(user_data.pop("password"))

        user = await self.user_repo.create(user_data)
        logger.info("Registered new user: %s", user.email)
        return user

    async def login(self, email: str, password: str) -> TokenPair:
        invalid_credentials = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise invalid_credentials

        if not verify_password(password, user.hashed_password):
            raise invalid_credentials

        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})

        logger.info("User logged in: %s", user.email)
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def refresh_tokens(self, refresh_token: str) -> TokenPair:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = decode_token(refresh_token, expected_type="refresh")
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None
        except jwt.InvalidTokenError:
            raise credentials_exception from None

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise credentials_exception

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )

        access_token = create_access_token(data={"sub": user.email})
        new_refresh_token = create_refresh_token(data={"sub": user.email})

        logger.info("User refreshed token: %s", user.email)
        return TokenPair(access_token=access_token, refresh_token=new_refresh_token)
