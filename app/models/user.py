import enum

from sqlalchemy import Boolean, Index, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    admin = "admin"
    warehouse_manager = "warehouse_manager"
    operator = "operator"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole"),
        nullable=False,
        default=UserRole.operator,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    stock_movements: Mapped[list["StockMovement"]] = relationship(  # noqa: F821
        back_populates="performed_by"
    )

    __table_args__ = (Index("ix_users_email", "email"),)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
