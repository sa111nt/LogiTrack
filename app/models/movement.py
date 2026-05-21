import enum

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class MovementType(str, enum.Enum):
    incoming = "IN"
    outgoing = "OUT"
    transfer = "TRANSFER"


class StockMovement(Base, TimestampMixin):
    """
    Immutable audit log of every inventory transaction.
    - IN: goods arrive at to_warehouse (from_warehouse is NULL).
    - OUT: goods leave from_warehouse (to_warehouse is NULL).
    - TRANSFER: goods move between two warehouses (both FKs required).
    """

    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    movement_type: Mapped[MovementType] = mapped_column(
        SAEnum(MovementType, name="movementtype"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    from_warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=True,
    )
    to_warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    product: Mapped["Product"] = relationship(  # noqa: F821
        back_populates="movements"
    )
    from_warehouse: Mapped["Warehouse | None"] = relationship(  # noqa: F821
        back_populates="outgoing_movements",
        foreign_keys=[from_warehouse_id],
    )
    to_warehouse: Mapped["Warehouse | None"] = relationship(  # noqa: F821
        back_populates="incoming_movements",
        foreign_keys=[to_warehouse_id],
    )
    performed_by: Mapped["User"] = relationship(  # noqa: F821
        back_populates="stock_movements"
    )

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_movement_quantity_positive"),
        Index("ix_stock_movements_product_id", "product_id"),
        Index("ix_stock_movements_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<StockMovement id={self.id} type={self.movement_type} "
            f"product_id={self.product_id} qty={self.quantity}>"
        )
