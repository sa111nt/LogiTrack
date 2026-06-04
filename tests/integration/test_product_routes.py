import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category_admin(
    async_client: AsyncClient, admin_headers: dict[str, str]
):
    response = await async_client.post(
        "/api/v1/categories/",
        json={"name": "Electronics", "description": "Test Category"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Electronics"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_category_unauthorized(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/categories/",
        json={"name": "Electronics", "description": "Test Category"},
    )
    # Should be 401 because no token was provided
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_product_admin(
    async_client: AsyncClient, admin_headers: dict[str, str]
):
    cat_resp = await async_client.post(
        "/api/v1/categories/",
        json={"name": "Laptops", "description": "Laptops"},
        headers=admin_headers,
    )
    category_id = cat_resp.json()["id"]

    prod_resp = await async_client.post(
        "/api/v1/products/",
        json={
            "sku": "LAPTOP-001",
            "name": "MacBook Pro",
            "description": "Apple Laptop",
            "category_id": category_id,
            "price": 2000.00,
        },
        headers=admin_headers,
    )
    assert prod_resp.status_code == 201
    data = prod_resp.json()
    assert data["sku"] == "LAPTOP-001"
    assert data["category_id"] == category_id


@pytest.mark.asyncio
async def test_list_products_filtering(
    async_client: AsyncClient, admin_headers: dict[str, str]
):
    # Using admin_headers because list_products requires authentication
    response = await async_client.get(
        "/api/v1/products/?category_id=9999",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("items", data) == []
