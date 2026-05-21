from sqlalchemy import Column, ForeignKey, Table

from app.models.base import Base

product_supplier = Table(
    "product_supplier",
    Base.metadata,
    Column(
        "product_id",
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "supplier_id",
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)
