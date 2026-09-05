import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idempotency import IdempotencyKey
from app.models.movement import StockMovement
from app.models.warehouse import Stock


async def _setup(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    wh_name: str,
    cat_name: str,
    sku: str,
    product_name: str,
) -> tuple[int, int]:
    wh = await client.post(
        "/api/v1/warehouses/",
        json={"name": wh_name, "location": "Test"},
        headers=headers,
    )
    cat = await client.post(
        "/api/v1/categories/",
        json={"name": cat_name, "description": "Test"},
        headers=headers,
    )
    prod = await client.post(
        "/api/v1/products/",
        json={
            "sku": sku,
            "name": product_name,
            "description": "Test",
            "category_id": cat.json()["id"],
            "price": 1.0,
        },
        headers=headers,
    )
    return wh.json()["id"], prod.json()["id"]


@pytest.mark.asyncio
async def test_idempotency_movement(
    async_client: AsyncClient,
    admin_headers: dict[str, str],
    test_db: AsyncSession,
) -> None:
    # Verifies that a duplicate request with the same idempotency key returns the cached response
    wh_id, prod_id = await _setup(
        async_client,
        admin_headers,
        wh_name="WH-Idem",
        cat_name="Cat-Idem",
        sku="IDEM-001",
        product_name="Idem Product",
    )

    idem_key = "idem-normal-001"
    payload = {
        "product_id": prod_id,
        "movement_type": "IN",
        "quantity": 25,
        "to_warehouse_id": wh_id,
    }

    r1 = await async_client.post(
        "/api/v1/stock/movements",
        json=payload,
        headers={**admin_headers, "Idempotency-Key": idem_key},
    )
    assert r1.status_code == 201

    r2 = await async_client.post(
        "/api/v1/stock/movements",
        json=payload,
        headers={**admin_headers, "Idempotency-Key": idem_key},
    )
    assert r2.status_code == 201
    assert r1.json() == r2.json()

    stock_resp = await async_client.get(
        f"/api/v1/stock/product/{prod_id}", headers=admin_headers
    )
    assert stock_resp.json()[0]["quantity"] == 25

    test_db.expire_all()
    movement_count = (
        await test_db.execute(
            select(func.count())
            .select_from(StockMovement)
            .where(StockMovement.product_id == prod_id)
        )
    ).scalar_one()
    assert movement_count == 1

    idem_count = (
        await test_db.execute(
            select(func.count())
            .select_from(IdempotencyKey)
            .where(IdempotencyKey.key == idem_key)
        )
    ).scalar_one()
    assert idem_count == 1


@pytest.mark.asyncio
async def test_idempotency_conflict_on_different_payload(
    async_client: AsyncClient,
    admin_headers: dict[str, str],
    test_db: AsyncSession,
) -> None:
    # Verifies that a request with the same key but different payload is rejected with 409 Conflict
    wh_id, prod_id = await _setup(
        async_client,
        admin_headers,
        wh_name="WH-Conf",
        cat_name="Cat-Conf",
        sku="CONF-001",
        product_name="Conflict Product",
    )

    idem_key = "idem-conflict-001"

    r1 = await async_client.post(
        "/api/v1/stock/movements",
        json={
            "product_id": prod_id,
            "movement_type": "IN",
            "quantity": 10,
            "to_warehouse_id": wh_id,
        },
        headers={**admin_headers, "Idempotency-Key": idem_key},
    )
    assert r1.status_code == 201

    r2 = await async_client.post(
        "/api/v1/stock/movements",
        json={
            "product_id": prod_id,
            "movement_type": "IN",
            "quantity": 99,
            "to_warehouse_id": wh_id,
        },
        headers={**admin_headers, "Idempotency-Key": idem_key},
    )
    assert r2.status_code == 409

    stock_resp = await async_client.get(
        f"/api/v1/stock/product/{prod_id}", headers=admin_headers
    )
    assert stock_resp.json()[0]["quantity"] == 10

    test_db.expire_all()
    movement_count = (
        await test_db.execute(
            select(func.count())
            .select_from(StockMovement)
            .where(StockMovement.product_id == prod_id)
        )
    ).scalar_one()
    assert movement_count == 1


@pytest.mark.asyncio
async def test_concurrent_out_select_for_update(
    async_client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    # Verifies that concurrent OUT requests are serialized via FOR UPDATE to prevent negative stock
    wh_id, prod_id = await _setup(
        async_client,
        admin_headers,
        wh_name="WH-ConcOUT",
        cat_name="Cat-ConcOUT",
        sku="COUT-001",
        product_name="ConcOUT Product",
    )

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

    async def request_out() -> int:
        resp = await async_client.post(
            "/api/v1/stock/movements",
            json={
                "product_id": prod_id,
                "movement_type": "OUT",
                "quantity": 6,
                "from_warehouse_id": wh_id,
            },
            headers=admin_headers,
        )
        return resp.status_code

    codes = await asyncio.gather(request_out(), request_out())

    assert 201 in codes
    assert codes.count(201) == 1
    assert 400 in codes

    stock_resp = await async_client.get(
        f"/api/v1/stock/product/{prod_id}", headers=admin_headers
    )
    assert stock_resp.json()[0]["quantity"] == 4


@pytest.mark.asyncio
async def test_concurrent_in_first_creation(
    async_client: AsyncClient,
    admin_headers: dict[str, str],
    test_db: AsyncSession,
) -> None:
    # Verifies that concurrent initial IN requests don't create duplicate Stock rows
    wh_id, prod_id = await _setup(
        async_client,
        admin_headers,
        wh_name="WH-ConcIN",
        cat_name="Cat-ConcIN",
        sku="CIN-001",
        product_name="ConcIN Product",
    )

    async def request_in(qty: int) -> int:
        resp = await async_client.post(
            "/api/v1/stock/movements",
            json={
                "product_id": prod_id,
                "movement_type": "IN",
                "quantity": qty,
                "to_warehouse_id": wh_id,
            },
            headers=admin_headers,
        )
        return resp.status_code

    codes = await asyncio.gather(request_in(10), request_in(20))
    assert codes == [201, 201]

    test_db.expire_all()
    rows = (
        (
            await test_db.execute(
                select(Stock).where(
                    Stock.product_id == prod_id,
                    Stock.warehouse_id == wh_id,
                )
            )
        )
        .scalars()
        .all()
    )

    assert len(rows) == 1
    assert rows[0].quantity == 30


@pytest.mark.asyncio
async def test_concurrent_same_idempotency_key(
    async_client: AsyncClient,
    admin_headers: dict[str, str],
    test_db: AsyncSession,
) -> None:
    # Verifies that concurrent requests with the same idempotency key run business logic exactly once
    wh_id, prod_id = await _setup(
        async_client,
        admin_headers,
        wh_name="WH-ConcIdem",
        cat_name="Cat-ConcIdem",
        sku="CIDEM-001",
        product_name="ConcIdem Product",
    )

    idem_key = "idem-concurrent-001"
    payload = {
        "product_id": prod_id,
        "movement_type": "IN",
        "quantity": 15,
        "to_warehouse_id": wh_id,
    }

    async def request() -> tuple[int, dict]:
        resp = await async_client.post(
            "/api/v1/stock/movements",
            json=payload,
            headers={**admin_headers, "Idempotency-Key": idem_key},
        )
        return resp.status_code, resp.json()

    results = await asyncio.gather(request(), request())
    codes = [r[0] for r in results]
    bodies = [r[1] for r in results]

    assert 201 in codes

    successful = [b for c, b in zip(codes, bodies, strict=True) if c == 201]
    if len(successful) == 2:
        assert successful[0] == successful[1]

    test_db.expire_all()
    rows = (
        (
            await test_db.execute(
                select(Stock).where(
                    Stock.product_id == prod_id,
                    Stock.warehouse_id == wh_id,
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].quantity == 15

    movement_count = (
        await test_db.execute(
            select(func.count())
            .select_from(StockMovement)
            .where(StockMovement.product_id == prod_id)
        )
    ).scalar_one()
    assert movement_count == 1

    idem_count = (
        await test_db.execute(
            select(func.count())
            .select_from(IdempotencyKey)
            .where(IdempotencyKey.key == idem_key)
        )
    ).scalar_one()
    assert idem_count == 1
