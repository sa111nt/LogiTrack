import asyncio
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_idempotency_movement(
    async_client: AsyncClient, admin_headers: dict[str, str]
):
    # Need to create a warehouse and product first
    wh_resp = await async_client.post(
        "/api/v1/warehouses/",
        json={"name": "WH-Idempotency", "location": "Test Loc"},
        headers=admin_headers,
    )
    wh_id = wh_resp.json()["id"]

    cat_resp = await async_client.post(
        "/api/v1/categories/",
        json={"name": "Test Cat", "description": "Test"},
        headers=admin_headers,
    )
    cat_id = cat_resp.json()["id"]

    prod_resp = await async_client.post(
        "/api/v1/products/",
        json={
            "sku": "IDEM-001",
            "name": "Idemp Product",
            "description": "Test",
            "category_id": cat_id,
            "price": 10.0,
        },
        headers=admin_headers,
    )
    prod_id = prod_resp.json()["id"]

    idempotency_key = "test-idem-key-123"

    # First request
    resp1 = await async_client.post(
        "/api/v1/stock/movements",
        json={
            "product_id": prod_id,
            "movement_type": "IN",
            "quantity": 10,
            "to_warehouse_id": wh_id,
            "notes": "First attempt",
        },
        headers={**admin_headers, "Idempotency-Key": idempotency_key},
    )
    assert resp1.status_code == 201

    # Second request with same idempotency key
    resp2 = await async_client.post(
        "/api/v1/stock/movements",
        json={
            "product_id": prod_id,
            "movement_type": "IN",
            "quantity": 10,
            "to_warehouse_id": wh_id,
            "notes": "First attempt",
        },
        headers={**admin_headers, "Idempotency-Key": idempotency_key},
    )
    assert resp2.status_code == 201
    assert resp1.json() == resp2.json()  # Exact same response

    # Verify stock is only 10, not 20
    stock_resp = await async_client.get(
        f"/api/v1/stock/product/{prod_id}",
        headers=admin_headers,
    )
    assert stock_resp.json()[0]["quantity"] == 10


@pytest.mark.asyncio
async def test_concurrent_movements(
    async_client: AsyncClient, admin_headers: dict[str, str]
):
    wh_resp = await async_client.post(
        "/api/v1/warehouses/",
        json={"name": "WH-Concurrent", "location": "Test Loc"},
        headers=admin_headers,
    )
    wh_id = wh_resp.json()["id"]

    cat_resp = await async_client.post(
        "/api/v1/categories/",
        json={"name": "Test Cat 2", "description": "Test"},
        headers=admin_headers,
    )
    cat_id = cat_resp.json()["id"]

    prod_resp = await async_client.post(
        "/api/v1/products/",
        json={
            "sku": "CONC-001",
            "name": "Concurrent Product",
            "description": "Test",
            "category_id": cat_id,
            "price": 10.0,
        },
        headers=admin_headers,
    )
    prod_id = prod_resp.json()["id"]

    # Initial stock IN: 10
    await async_client.post(
        "/api/v1/stock/movements",
        json={
            "product_id": prod_id,
            "movement_type": "IN",
            "quantity": 10,
            "to_warehouse_id": wh_id,
        },
        headers=admin_headers,
    )

    # 2 concurrent OUT requests of 6 each. Since stock is 10, only one should succeed
    async def request_out():
        return await async_client.post(
            "/api/v1/stock/movements",
            json={
                "product_id": prod_id,
                "movement_type": "OUT",
                "quantity": 6,
                "from_warehouse_id": wh_id,
            },
            headers=admin_headers,
        )

    results = await asyncio.gather(request_out(), request_out())
    status_codes = [r.status_code for r in results]

    # We expect one 201 and one 400 (Insufficient stock)
    # The database CHECK(quantity >= 0) constraint will cause a rollback on the second one
    # Project doesnt have SELECT FOR UPDATE, so the CHECK constraint is what triggers the error (IntegrityError).
    # Depending on how the error is caught, it might be 400 or 500, but one must fail.
    assert 201 in status_codes
    assert status_codes.count(201) == 1

    # Verify stock is 4
    stock_resp = await async_client.get(
        f"/api/v1/stock/product/{prod_id}",
        headers=admin_headers,
    )
    assert stock_resp.json()[0]["quantity"] == 4
