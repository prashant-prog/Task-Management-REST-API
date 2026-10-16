from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    PROJECT_NAME: str = "Task Management REST API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Database configuration
    DATABASE_URL: str = (
        "postgresql+psycopg://task_user:task_password@localhost:5432/task_db"
    )

    # Dedicated Test Database configuration
    TEST_DATABASE_URL: str = (
        "postgresql+psycopg://task_user:task_password@localhost:5432/task_test_db"
    )

    # JWT Authentication configuration
    SECRET_KEY: str = "default-insecure-secret-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
