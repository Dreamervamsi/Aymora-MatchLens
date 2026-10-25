"""
API configuration management.
"""

import os
from pydantic import BaseModel, Field


class APISettings(BaseModel):
    api_v1_prefix: str = "/api/v1"
    title: str = "MatchLens API"
    description: str = "Scenario-aware reciprocal compatibility and onboarding backend API"
    version: str = "1.0.0"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])


settings = APISettings()

