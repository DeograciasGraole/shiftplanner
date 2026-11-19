from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import (
    Uuid,
    String,
    Integer,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
    CheckConstraint,
    Index,
    func,
)
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=True,
        index=True,
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
    )
    password_hash:Mapped[str|None]=mapped_column(
        String(120),
        nullable=True,
    )
    employee_id: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )
    

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="employee",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="invited",
    )

    hourly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    site_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    activation_code_hash: Mapped[str | None] = mapped_column(String(255))
    activation_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan",
)
    password_reset_codes: Mapped[list["PasswordResetCode"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan",
)
