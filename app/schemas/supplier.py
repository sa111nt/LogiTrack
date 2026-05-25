import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import OrmBase


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    contact_email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None


class SupplierRead(OrmBase):
    id: int
    name: str
    contact_email: str | None
    phone: str | None
    address: str | None
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    contact_email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    is_active: bool | None = None
