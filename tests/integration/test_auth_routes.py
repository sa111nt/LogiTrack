import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@test.com",
            "password": "securepassword",
            "full_name": "New Test User",
            "role": "operator",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["full_name"] == "New Test User"
    assert data["is_active"] is True
    assert "password" not in data


@pytest.mark.asyncio
async def test_login_user(async_client: AsyncClient):
    # Register first
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "loginuser@test.com",
            "password": "securepassword",
            "full_name": "Login Test User",
            "role": "operator",
        },
    )

    # Now login using form data
    response = await async_client.post(
        "/api/v1/auth/login",
        data={
            "username": "loginuser@test.com",
            "password": "securepassword",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_me(async_client: AsyncClient, admin_headers: dict[str, str]):
    response = await async_client.get(
        "/api/v1/auth/me",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_logout_and_revocation(async_client: AsyncClient):
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "logoutuser@test.com",
            "password": "securepassword",
            "full_name": "Logout Test User",
            "role": "operator",
        },
    )

    login_resp = await async_client.post(
        "/api/v1/auth/login",
        data={
            "username": "logoutuser@test.com",
            "password": "securepassword",
        },
    )
    tokens = login_resp.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Verify token works before logout
    me_resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200

    # Logout
    logout_resp = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers=headers,
    )
    assert logout_resp.status_code == 204

    # Verify access token is revoked
    me_resp_after = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_resp_after.status_code == 401

    # Verify refresh token is also revoked
    refresh_resp = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 401
