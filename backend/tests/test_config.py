"""Unit tests for configuration module."""
import pytest
from pydantic import ValidationError
from app.config import Settings, get_settings


def test_default_test_settings() -> None:
    """Verify test configuration values loaded from fixtures."""
    settings = get_settings()
    assert settings.APP_ENV == "testing"
    assert settings.is_testing is True
    assert settings.LLM_PROVIDER == "mock"
    assert settings.DATABASE_URL == "sqlite:///:memory:"


def test_invalid_temperature_raises_validation_error() -> None:
    """Verify validation fails if LLM_TEMPERATURE is out of bounds [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        Settings(LLM_TEMPERATURE=2.5)


def test_invalid_port_raises_validation_error() -> None:
    """Verify validation fails if APP_PORT is out of bounds [1, 65535]."""
    with pytest.raises(ValidationError):
        Settings(APP_PORT=70000)


def test_custom_settings_instantiation() -> None:
    """Verify explicit settings instantiation overrides environment variables."""
    custom = Settings(
        APP_ENV="development",
        LLM_PROVIDER="openai",
        LLM_MODEL="gpt-4o",
        MAX_DIFF_CHARACTERS=20000,
    )
    assert custom.APP_ENV == "development"
    assert custom.is_testing is False
    assert custom.LLM_PROVIDER == "openai"
    assert custom.LLM_MODEL == "gpt-4o"
    assert custom.MAX_DIFF_CHARACTERS == 20000
