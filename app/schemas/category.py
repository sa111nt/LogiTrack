import datetime

from pydantic import BaseModel, Field

from app.schemas.base import OrmBase


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class CategoryRead(OrmBase):
    id: int
    name: str
    description: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
