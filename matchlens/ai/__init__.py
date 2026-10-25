"""
MatchLens AI Integration Package (Groq AI Integration Foundation).
"""

from matchlens.ai.config import GroqSettings
from matchlens.ai.exceptions import (
    GroqError,
    GroqMissingKeyError,
    GroqAPIError,
    GroqPermanentAPIError,
    GroqTimeoutError,
    GroqValidationError,
)
from matchlens.ai.models import (
    FieldExtraction,
    PartialUserAttributes,
    PartialPartnerPreferences,
    PartialDealbreakers,
    ConfirmationPrompt,
    ExtractedProfileUpdate,
)
from matchlens.ai.client import GroqClient
from matchlens.ai.extractor import GroqProfileExtractor

__all__ = [
    "GroqSettings",
    "GroqError",
    "GroqMissingKeyError",
    "GroqAPIError",
    "GroqPermanentAPIError",
    "GroqTimeoutError",
    "GroqValidationError",
    "FieldExtraction",
    "PartialUserAttributes",
    "PartialPartnerPreferences",
    "PartialDealbreakers",
    "ConfirmationPrompt",
    "ExtractedProfileUpdate",
    "GroqClient",
    "GroqProfileExtractor",
]
