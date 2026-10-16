from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base schema containing shared user attributes."""

    email: EmailStr = Field(..., description="Unique email address")


class UserCreate(UserBase):
    """Schema for user registration requests."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (minimum 8 characters)",
    )


class UserResponse(UserBase):
    """Public user schema returned in API responses.

    Excludes sensitive fields like hashed_password.
    """

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # from_attributes=True allows Pydantic to serialize SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)
