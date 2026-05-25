import datetime

from pydantic import BaseModel, Field

from app.models.movement import MovementType
from app.schemas.base import OrmBase


class StockRead(OrmBase):
    id: int
    product_id: int
    warehouse_id: int
    quantity: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class StockMovementCreate(BaseModel):
    movement_type: MovementType
    product_id: int
    from_warehouse_id: int | None = None
    to_warehouse_id: int | None = None
    quantity: int = Field(gt=0)
    notes: str | None = None


class StockMovementRead(OrmBase):
    id: int
    movement_type: MovementType
    product_id: int
    from_warehouse_id: int | None
    to_warehouse_id: int | None
    quantity: int
    notes: str | None
    performed_by_id: int
    created_at: datetime.datetime
