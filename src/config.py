"""Configuration management using Pydantic Settings."""

from pathlib import Path

import logfire
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database settings
    tinydb_path: Path = Field(
        default=Path("tinydb_data.json"),
        description="Path to the TinyDB database file",
    )

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    enable_logfire: bool = Field(
        default=False,
        description="Enable Logfire structured logging (requires API token)",
    )
    logfire_token: str | None = Field(
        default=None,
        description="Logfire API token for remote logging",
    )

    # MCP Server settings
    server_name: str = Field(
        default="TinyDB MCP Server",
        description="Name of the MCP server",
    )
    server_version: str = Field(
        default="0.1.0",
        description="Version of the MCP server",
    )


# Global settings instance
settings = Settings()


def configure_logging() -> None:
    """Configure logfire based on settings."""
    if settings.enable_logfire and settings.logfire_token:
        logfire.configure(token=settings.logfire_token)
        logfire.info("Logfire configured", settings=settings.model_dump(exclude={"logfire_token"}))
    else:
        # Configure logfire for local development (no remote sending)
        logfire.configure(send_to_logfire=False)
        logfire.info("Logfire configured (local only)", log_level=settings.log_level)
