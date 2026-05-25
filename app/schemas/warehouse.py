import datetime

from pydantic import BaseModel, Field

from app.schemas.base import OrmBase


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=500)
    description: str | None = None


class WarehouseRead(OrmBase):
    id: int
    name: str
    location: str | None
    description: str | None
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=500)
    description: str | None = None
    is_active: bool | None = None
