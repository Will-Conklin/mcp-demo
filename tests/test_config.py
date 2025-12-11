"""Configuration and settings tests.

These tests validate the Pydantic Settings configuration, environment variable
loading, logging setup, and configuration validation.
"""

import os
from pathlib import Path

from src.config import Settings, configure_logging


class TestSettingsValidation:
    """Tests for Settings model validation and configuration."""

    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        settings = Settings()

        assert settings.tinydb_path == Path("tinydb_data.json")
        assert settings.log_level == "INFO"
        assert settings.enable_logfire is False
        assert settings.logfire_token is None
        assert settings.server_name == "TinyDB MCP Server"
        assert settings.server_version == "0.1.0"

    def test_settings_from_env_vars(self, monkeypatch):
        """Test loading settings from environment variables."""
        # Set environment variables
        monkeypatch.setenv("TINYDB_PATH", "/custom/path/db.json")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("ENABLE_LOGFIRE", "true")
        monkeypatch.setenv("LOGFIRE_TOKEN", "test-token-123")
        monkeypatch.setenv("SERVER_NAME", "Custom Server")
        monkeypatch.setenv("SERVER_VERSION", "1.0.0")

        # Create new settings instance (will read from env vars)
        settings = Settings()

        assert settings.tinydb_path == Path("/custom/path/db.json")
        assert settings.log_level == "DEBUG"
        assert settings.enable_logfire is True
        assert settings.logfire_token == "test-token-123"
        assert settings.server_name == "Custom Server"
        assert settings.server_version == "1.0.0"

    def test_settings_from_dotenv(self, tmp_path):
        """Test loading settings from .env file."""
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
TINYDB_PATH=test_data.json
LOG_LEVEL=WARNING
ENABLE_LOGFIRE=false
SERVER_NAME=Test Server
"""
        )

        # Change to temp directory and load settings
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            settings = Settings()

            assert settings.tinydb_path == Path("test_data.json")
            assert settings.log_level == "WARNING"
            assert settings.enable_logfire is False
            assert settings.server_name == "Test Server"
        finally:
            os.chdir(original_dir)

    def test_case_insensitive_env_vars(self, monkeypatch):
        """Test that environment variables are case-insensitive."""
        # Set lowercase environment variables
        monkeypatch.setenv("tinydb_path", "/lowercase/path.json")
        monkeypatch.setenv("log_level", "error")

        settings = Settings()

        assert settings.tinydb_path == Path("/lowercase/path.json")
        assert settings.log_level == "error"

    def test_path_field_validation(self):
        """Test that tinydb_path is converted to Path object."""
        settings = Settings(tinydb_path="string/path.json")  # type: ignore[arg-type]

        assert isinstance(settings.tinydb_path, Path)
        assert settings.tinydb_path == Path("string/path.json")

    def test_boolean_field_validation(self, monkeypatch):
        """Test boolean field parsing from strings."""
        # Test various boolean string representations
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
        ]

        for env_value, expected in test_cases:
            monkeypatch.setenv("ENABLE_LOGFIRE", env_value)
            settings = Settings()
            assert settings.enable_logfire is expected

    def test_environment_variable_precedence(self, tmp_path, monkeypatch):
        """Test that environment variables take precedence over .env file."""
        # Create .env file with one value
        env_file = tmp_path / ".env"
        env_file.write_text("LOG_LEVEL=INFO\n")

        # Set environment variable with different value
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            settings = Settings()

            # Environment variable should take precedence
            assert settings.log_level == "DEBUG"
        finally:
            os.chdir(original_dir)

    def test_optional_logfire_token(self):
        """Test that logfire_token is optional and defaults to None."""
        settings = Settings()

        assert settings.logfire_token is None

        # Test with token set
        settings_with_token = Settings(logfire_token="test-token")
        assert settings_with_token.logfire_token == "test-token"

    def test_extra_fields_ignored(self, monkeypatch):
        """Test that extra unknown fields are ignored."""
        monkeypatch.setenv("UNKNOWN_FIELD", "some_value")
        monkeypatch.setenv("ANOTHER_UNKNOWN", "another_value")

        # Should not raise validation error
        settings = Settings()

        # Should still have default values
        assert settings.tinydb_path == Path("tinydb_data.json")

    def test_model_dump_excludes_secrets(self):
        """Test that model_dump can exclude sensitive fields."""
        settings = Settings(logfire_token="secret-token-123")

        # Dump without token
        dump = settings.model_dump(exclude={"logfire_token"})

        assert "logfire_token" not in dump
        assert dump["tinydb_path"] == Path("tinydb_data.json")
        assert dump["server_name"] == "TinyDB MCP Server"


class TestLoggingConfiguration:
    """Tests for logging configuration."""

    def test_configure_logging_local_mode(self, monkeypatch):
        """Test logging configuration in local mode (no remote sending)."""
        # Ensure logfire is disabled
        monkeypatch.setenv("ENABLE_LOGFIRE", "false")

        settings = Settings()
        assert settings.enable_logfire is False

        # Should not raise error
        configure_logging()

    def test_configure_logging_with_logfire_disabled(self, monkeypatch):
        """Test that logfire local mode is used when disabled."""
        monkeypatch.setenv("ENABLE_LOGFIRE", "false")
        monkeypatch.setenv("LOGFIRE_TOKEN", "token-exists-but-disabled")

        settings = Settings()

        # Even with token, if enable_logfire is False, use local mode
        assert settings.enable_logfire is False
        configure_logging()

    def test_configure_logging_enabled_without_token(self, monkeypatch):
        """Test logging configuration when enabled but no token provided."""
        monkeypatch.setenv("ENABLE_LOGFIRE", "true")
        monkeypatch.delenv("LOGFIRE_TOKEN", raising=False)

        settings = Settings()
        assert settings.enable_logfire is True
        assert settings.logfire_token is None

        # Should use local mode if no token
        configure_logging()

    def test_log_level_configuration(self, monkeypatch):
        """Test different log level configurations."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            monkeypatch.setenv("LOG_LEVEL", level)
            settings = Settings()
            assert settings.log_level == level
