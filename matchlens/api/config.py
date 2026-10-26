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
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "MATCHLENS_CORS_ORIGINS",
                "https://aymora-match-lens.vercel.app,"
                "https://grim-spooky-skull-5wjgxvggqppfwr4-3000.app.github.dev,"
                "https://grim-spooky-skull-5wjgxvggqppfwr4-8000.app.github.dev,"
                "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000",
            ).split(",")
            if origin.strip()
        ]
    )
    cors_origin_regex: str = Field(
        default_factory=lambda: os.getenv(
            "MATCHLENS_CORS_ORIGIN_REGEX",
            r"https://.*\.vercel\.app|https://.*\.app\.github\.dev|http://localhost:\d+|http://127\.0\.0\.1:\d+",
        )
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])


settings = APISettings()

