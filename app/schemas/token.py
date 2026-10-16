from pydantic import BaseModel, Field


class Token(BaseModel):
    """Schema returned to client upon successful login."""

    access_token: str = Field(..., description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Token authentication scheme")


class TokenPayload(BaseModel):
    """Schema representing validated JWT token claims."""

    sub: str | None = None
