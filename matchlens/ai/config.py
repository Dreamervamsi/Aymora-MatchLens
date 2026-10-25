import os
from typing import Optional
from pydantic import BaseModel, Field


class GroqSettings(BaseModel):
    """
    Configuration settings for Groq AI model integration.
    Reads API key from environment variable GROQ_API_KEY.
    """
    api_key_env_var: str = Field(default="GROQ_API_KEY", description="Environment variable name for Groq API key")
    model_name: str = Field(default="openai/gpt-oss-120b", description="Groq model identifier")
    timeout_seconds: float = Field(default=10.0, ge=0.01, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts on transient failures")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Sampling temperature for extraction")

    def get_api_key(self) -> Optional[str]:
        """
        Retrieves API key from environment variable.
        """
        return os.environ.get(self.api_key_env_var)
