from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.movement import StockMovement
    from app.models.supplier import Supplier
    from app.models.warehouse import Stock


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    category: Mapped["Category | None"] = relationship(back_populates="products")
    suppliers: Mapped[list["Supplier"]] = relationship(
        secondary="product_supplier",
        back_populates="products",
    )
    stock_entries: Mapped[list["Stock"]] = relationship(back_populates="product")
    movements: Mapped[list["StockMovement"]] = relationship(back_populates="product")

    __table_args__ = (Index("ix_products_sku", "sku"),)

    def __repr__(self) -> str:
        return f"<Product id={self.id} sku={self.sku!r} name={self.name!r}>"
