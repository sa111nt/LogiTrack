from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Warehouse(Base, TimestampMixin):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    stock_entries: Mapped[list["Stock"]] = relationship(back_populates="warehouse")
    outgoing_movements: Mapped[list["StockMovement"]] = relationship(  # noqa: F821
        back_populates="from_warehouse",
        foreign_keys="StockMovement.from_warehouse_id",
    )
    incoming_movements: Mapped[list["StockMovement"]] = relationship(  # noqa: F821
        back_populates="to_warehouse",
        foreign_keys="StockMovement.to_warehouse_id",
    )

    def __repr__(self) -> str:
        return f"<Warehouse id={self.id} name={self.name!r}>"


class Stock(Base, TimestampMixin):
    """
    Current inventory level for a specific Product at a specific Warehouse.
    The unique constraint ensures there is exactly one Stock record
    per product-warehouse combination.
    """

    __tablename__ = "stock"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    product: Mapped["Product"] = relationship(  # noqa: F821
        back_populates="stock_entries"
    )
    warehouse: Mapped["Warehouse"] = relationship(back_populates="stock_entries")

    __table_args__ = (
        UniqueConstraint(
            "product_id", "warehouse_id", name="uq_stock_product_warehouse"
        ),
        CheckConstraint("quantity >= 0", name="ck_stock_quantity_non_negative"),
    )

    def __repr__(self) -> str:
        return (
            f"<Stock product_id={self.product_id} "
            f"warehouse_id={self.warehouse_id} qty={self.quantity}>"
        )
