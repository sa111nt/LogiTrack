import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.schemas.base import OrmBase
from app.schemas.category import CategoryRead


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(ge=0, decimal_places=2)
    category_id: int | None = None

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, v: str) -> str:
        return v.strip().upper()


class ProductRead(OrmBase):
    id: int
    sku: str
    name: str
    description: str | None
    price: Decimal
    is_active: bool
    category_id: int | None
    category: CategoryRead | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    is_active: bool | None = None
    category_id: int | None = None
