from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_async_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.base import Base
from app.models.user import User, UserRole

PG_TEST_URL = (
    "postgresql+asyncpg://logitrack_user:secretpassword@localhost:5432/logitrack_test"
)
PG_ROOT_URL = (
    "postgresql+asyncpg://logitrack_user:secretpassword@localhost:5432/logitrack_db"
)

_test_db_ready: bool = False


@pytest_asyncio.fixture(scope="function")
async def pg_session_factory():
    global _test_db_ready
    engine = create_async_engine(PG_TEST_URL, echo=False)
    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    if not _test_db_ready:
        root_engine = create_async_engine(PG_ROOT_URL, isolation_level="AUTOCOMMIT")
        async with root_engine.connect() as conn:
            row = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'logitrack_test'")
            )
            if not row.fetchone():
                await conn.execute(text("CREATE DATABASE logitrack_test"))
        await root_engine.dispose()
        _test_db_ready = True

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(pg_session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with pg_session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def async_client(pg_session_factory) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with pg_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_async_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def admin_user(test_db: AsyncSession) -> User:
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("admin_pass"),
        full_name="Test Admin",
        role=UserRole.admin,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def admin_token(admin_user: User) -> str:
    return create_access_token({"sub": admin_user.email})


@pytest_asyncio.fixture(scope="function")
async def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}
