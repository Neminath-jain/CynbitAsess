"""Configuration settings for BitElevate PR Review Copilot.

Loads settings from environment variables using pydantic-settings.
Secrets are never hardcoded and must be provided via the environment.
"""
from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings validated via Pydantic."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application Core
    APP_ENV: Literal["development", "testing", "production"] = "development"
    APP_PORT: int = Field(default=8000, ge=1, le=65535)
    APP_HOST: str = "0.0.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(
        default="change-this-in-production-to-a-secure-random-string",
        min_length=16,
    )

    # Persistence
    DATABASE_URL: str = "sqlite:///./bitelevate_copilot.db"

    # LLM Provider Configuration
    LLM_PROVIDER: Literal["openai", "gemini", "mock"] = "mock"
    LLM_API_KEY: str = Field(default="", description="API key for the active LLM provider")
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_TEMPERATURE: float = Field(default=0.1, ge=0.0, le=1.0)
    LLM_MAX_TOKENS: int = Field(default=2500, ge=100, le=8000)

    # GitHub Integration
    GITHUB_TOKEN: str = Field(default="", description="Personal access token or bot token for GitHub API")
    GITHUB_WEBHOOK_SECRET: str = Field(default="", description="Secret HMAC key for validating GitHub webhook payloads")

    # Guardrails & Budgets
    MAX_DIFF_CHARACTERS: int = Field(default=50000, ge=1000)
    MAX_DIFF_FILES: int = Field(default=25, ge=1)
    MAX_COMMENTS_PER_REVIEW: int = Field(default=15, ge=1)
    ENABLE_PROMPT_INJECTION_DEFENSE: bool = True

    @property
    def is_testing(self) -> bool:
        """Helper to verify if running in testing mode."""
        return self.APP_ENV == "testing"


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of Settings."""
    return Settings()
