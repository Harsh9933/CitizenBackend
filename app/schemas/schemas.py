from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.models import UserRole, ComplaintStatus, Priority


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user creation."""
    role: Optional[UserRole] = UserRole.USER
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    role: UserRole

    class Config:
        from_attributes = True


# Auth Schemas
class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[int] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


# Complaint Schemas
class ComplaintBase(BaseModel):
    """Base complaint schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class ComplaintCreate(ComplaintBase):
    """Schema for creating a complaint."""
    image_url: Optional[str] = Field(None, max_length=500)
    priority: Priority = Priority.MEDIUM


class ComplaintUpdate(BaseModel):
    """Schema for updating complaint status."""
    status: Optional[ComplaintStatus] = None
    priority: Optional[Priority] = None


class ImageUpload(BaseModel):
    """Schema for uploading image URL."""
    image_url: str = Field(..., max_length=500)


class ComplaintResponse(ComplaintBase):
    """Schema for complaint response."""
    id: int
    user_id: int
    image_url: Optional[str]
    status: ComplaintStatus
    priority: Priority
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplaintListResponse(BaseModel):
    """Schema for paginated complaint list."""
    items: list[ComplaintResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ComplaintFilter(BaseModel):
    """Schema for filtering complaints."""
    status: Optional[ComplaintStatus] = None
    priority: Optional[Priority] = None