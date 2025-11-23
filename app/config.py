"""
Application configuration management using Pydantic Settings.
"""

from typing import List, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    See .env.example for all available options.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application Settings
    app_name: str = Field(default="tool-calling-agent", description="Application name")
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Runtime environment"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )

    # LLM Provider Configuration
    default_llm_provider: Literal["openai", "anthropic"] = Field(
        default="openai",
        description="Default LLM provider to use"
    )

    # OpenAI Configuration
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI model to use"
    )

    # Anthropic Configuration
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Anthropic model to use"
    )

    # Agent Configuration
    max_tool_calls_per_turn: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum tool calls allowed per turn (prevents infinite loops)"
    )
    tool_call_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Timeout for individual tool execution"
    )
    enable_tool_validation: bool = Field(
        default=True,
        description="Enable tool output validation"
    )

    # API Configuration
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API v1 route prefix"
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable rate limiting"
    )
    rate_limit_requests_per_minute: int = Field(
        default=60,
        ge=1,
        description="Maximum requests per minute per client"
    )

    @field_validator("openai_api_key", "anthropic_api_key")
    @classmethod
    def validate_api_keys(cls, v: str, info) -> str:
        """Validate that API keys are provided when needed."""
        # In development, empty keys are allowed for testing
        if not v and info.data.get("environment") == "production":
            field_name = info.field_name
            raise ValueError(
                f"{field_name} must be provided in production environment"
            )
        return v

    def get_provider_config(self, provider: str) -> dict:
        """
        Get configuration for a specific provider.

        Args:
            provider: Provider name ('openai' or 'anthropic')

        Returns:
            Dictionary with provider-specific configuration
        """
        if provider == "openai":
            return {
                "api_key": self.openai_api_key,
                "model": self.openai_model,
            }
        elif provider == "anthropic":
            return {
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model,
            }
        else:
            raise ValueError(f"Unknown provider: {provider}")


# Global settings instance
settings = Settings()
