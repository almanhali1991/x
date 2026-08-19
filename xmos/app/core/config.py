"""
Core configuration management for XMOS.

Loads settings from environment variables with validation.
"""

from functools import lru_cache
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------
    # Application Settings
    # -------------------------------------------
    app_env: str = Field(default="development", description="Environment name")
    app_debug: bool = Field(default=True, description="Debug mode")
    app_host: str = Field(default="127.0.0.1", description="Host to bind")
    app_port: int = Field(default=8000, description="Port to bind")
    app_timezone: str = Field(default="Asia/Riyadh", description="Default timezone")

    # -------------------------------------------
    # Database
    # -------------------------------------------
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/xmos.db",
        description="Database connection URL",
    )

    # -------------------------------------------
    # X (Twitter) API Credentials
    # -------------------------------------------
    x_api_key: str | None = Field(default=None, description="X API Key")
    x_api_secret: str | None = Field(default=None, description="X API Secret")
    x_access_token: str | None = Field(default=None, description="X Access Token")
    x_access_token_secret: str | None = Field(
        default=None, description="X Access Token Secret"
    )
    x_bearer_token: str | None = Field(default=None, description="X Bearer Token")
    x_client_id: str | None = Field(default=None, description="X Client ID")
    x_client_secret: str | None = Field(default=None, description="X Client Secret")
    x_callback_url: str = Field(
        default="http://localhost:8000/api/x/callback",
        description="OAuth callback URL",
    )

    # -------------------------------------------
    # DeepSeek AI API
    # -------------------------------------------
    deepseek_api_key: str | None = Field(
        default=None, description="DeepSeek API Key"
    )
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com", description="DeepSeek API Base URL"
    )
    deepseek_model: str = Field(
        default="deepseek-chat", description="DeepSeek Model Name"
    )

    # -------------------------------------------
    # Content Limits & Budget Guards
    # -------------------------------------------
    max_ai_posts_per_day: int = Field(default=5, ge=0, le=20)
    max_ai_threads_per_day: int = Field(default=2, ge=0, le=10)
    max_trend_scans_per_day: int = Field(default=3, ge=1, le=10)
    max_watchlist_accounts: int = Field(default=10, ge=1, le=20)
    max_monthly_ai_budget: float = Field(default=100.0, ge=0.0)
    max_monthly_x_api_budget: float = Field(default=100.0, ge=0.0)

    # -------------------------------------------
    # Security
    # -------------------------------------------
    secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret key for sessions and tokens",
    )
    dashboard_admin_username: str = Field(default="admin")
    dashboard_admin_password: str = Field(default="admin")

    # -------------------------------------------
    # Logging
    # -------------------------------------------
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="data/xmos.log", description="Log file path")

    # -------------------------------------------
    # Backup Settings
    # -------------------------------------------
    backup_dir: str = Field(default="./data/backups", description="Backup directory")
    backup_retention_days: int = Field(default=30, ge=1, le=365)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"

    def validate_credentials(self) -> dict[str, list[str]]:
        """Validate that required credentials are present."""
        errors: dict[str, list[str]] = {"x_api": [], "deepseek": []}

        # X API credentials (at minimum need OAuth or v2 bearer token)
        if not self.x_client_id or not self.x_client_secret:
            errors["x_api"].append("X Client ID and Secret are required for OAuth")

        # DeepSeek API
        if not self.deepseek_api_key:
            errors["deepseek"].append("DeepSeek API Key is required")

        return errors


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience exports
settings = get_settings()


def reload_settings() -> Settings:
    """Force reload settings (useful for testing)."""
    return get_settings.cache_clear() or get_settings()  # type: ignore
