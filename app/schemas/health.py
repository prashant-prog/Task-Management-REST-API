from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Schema for health-check endpoint response."""

    status: str = Field(..., description="Current service health status")
    app_name: str = Field(..., description="Application name")
    environment: str = Field(..., description="Active runtime environment")
    database: str = Field(..., description="Database connectivity status")
