from datetime import datetime
from sqlalchemy import String, Text, Float, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"


class ComplaintStatus(str, enum.Enum):
    """Complaint status enumeration."""
    PENDING = "pending"
    VERIFIED = "verified"
    RESOLVED = "resolved"


class Priority(str, enum.Enum):
    """Complaint priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class User(Base):
    """User model."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default=UserRole.USER.value, nullable=False)

    # Relationships
    complaints: Mapped[list["Complaint"]] = relationship("Complaint", back_populates="user")


class Complaint(Base):
    """Complaint model."""
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ComplaintStatus] = mapped_column(
        SQLEnum(ComplaintStatus),
        default=ComplaintStatus.PENDING,
        nullable=False,
        index=True
    )
    priority: Mapped[Priority] = mapped_column(
        SQLEnum(Priority),
        default=Priority.MEDIUM,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="complaints")