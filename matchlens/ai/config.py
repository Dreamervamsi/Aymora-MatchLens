import os
from typing import Optional
from pydantic import BaseModel, Field


class GroqSettings(BaseModel):
    """
    Configuration settings for Groq AI model integration.
    Reads settings from environment variables with sensible defaults.
    """
    api_key_env_var: str = Field(default="GROQ_API_KEY", description="Environment variable name for Groq API key")
    model_name: str = Field(
        default_factory=lambda: os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant"),
        description="Groq model identifier",
    )
    timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("GROQ_TIMEOUT_SECONDS", "60.0")),
        ge=0.01,
        description="Request timeout in seconds",
    )
    max_retries: int = Field(
        default_factory=lambda: int(os.getenv("GROQ_MAX_RETRIES", "3")),
        ge=0,
        description="Maximum retry attempts on transient failures",
    )
    temperature: float = Field(
        default_factory=lambda: float(os.getenv("GROQ_TEMPERATURE", "0.1")),
        ge=0.0,
        le=2.0,
        description="Sampling temperature for extraction",
    )

    def get_api_key(self) -> Optional[str]:
        """
        Retrieves API key from environment variable.
        """
        return os.environ.get(self.api_key_env_var)
