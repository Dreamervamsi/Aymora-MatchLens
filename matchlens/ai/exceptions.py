class GroqError(Exception):
    """Base exception for all Groq AI integration errors."""
    pass


class GroqMissingKeyError(GroqError):
    """Raised when GROQ_API_KEY environment variable is not set."""
    pass


class GroqAPIError(GroqError):
    """Raised when Groq API request fails due to network or provider error."""
    pass


class GroqPermanentAPIError(GroqAPIError):
    """Raised when Groq API fails with permanent 4xx error (401, 400, 403, 404). Should not be retried."""
    pass


class GroqTimeoutError(GroqError):
    """Raised when Groq API call times out."""
    pass


class GroqValidationError(GroqError):
    """Raised when model response fails Pydantic schema validation."""
    pass
