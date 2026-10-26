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
<<<<<<< HEAD
        default_factory=lambda: os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant"),
=======
        default_factory=lambda: os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-20b"),
>>>>>>> 2cf62f4 (fix unncessary llm calls)
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
    max_tokens: Optional[int] = Field(
        default_factory=lambda: int(os.getenv("GROQ_MAX_TOKENS", "1024")) if os.getenv("GROQ_MAX_TOKENS") else 1024,
        ge=1,
        description="Maximum tokens allowed in generated output response to prevent excessive token usage",
    )
    reasoning_effort: Optional[str] = Field(
        default_factory=lambda: os.getenv("GROQ_REASONING_EFFORT", "low"),
        description="Reasoning effort level for reasoning models (e.g., low, medium, high)",
    )

    def get_api_key(self) -> Optional[str]:
        """
        Retrieves API key from environment variable.
        """
        return os.environ.get(self.api_key_env_var)
