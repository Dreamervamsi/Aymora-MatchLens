import asyncio
import json
import logging
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError

from groq import (
    AsyncGroq,
    APIError,
    APIConnectionError,
    RateLimitError,
    AuthenticationError,
    BadRequestError,
    PermissionDeniedError,
    NotFoundError,
)
from matchlens.ai.config import GroqSettings
from matchlens.ai.exceptions import (
    GroqError,
    GroqMissingKeyError,
    GroqAPIError,
    GroqPermanentAPIError,
    GroqTimeoutError,
    GroqValidationError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

PERMANENT_ERROR_CLASSES = (
    AuthenticationError,
    BadRequestError,
    PermissionDeniedError,
    NotFoundError,
)


class GroqClient:
    """
    Asynchronous client wrapper for Groq AI service.
    Handles API authentication, structured JSON output enforcement (with json_schema fallback),
    timeouts, transient retry logic with exponential backoff, and strict Pydantic validation.
    """

    def __init__(
        self,
        settings: Optional[GroqSettings] = None,
        client: Optional[AsyncGroq] = None,
    ):
        self.settings = settings or GroqSettings()
        api_key = self.settings.get_api_key()

        if not api_key and client is None:
            raise GroqMissingKeyError(
                f"Groq API key not found in environment variable '{self.settings.api_key_env_var}'."
            )

        self._client = client or AsyncGroq(api_key=api_key)

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Type[T],
    ) -> T:
        """
        Sends prompt to Groq API expecting structured JSON output conforming to response_schema.
        Applies timeout, transient retry logic with backoff, and local Pydantic validation.
        """
        json_schema = response_schema.model_json_schema()
        schema_instruction = (
            f"\n\nReturn ONLY a valid JSON object matching this exact JSON schema:\n"
            f"{json.dumps(json_schema, indent=2)}\n"
            "Do not include markdown code block formatting (e.g. ```json), commentary, or extra text."
        )

        full_system = system_instruction + schema_instruction
        current_messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": prompt},
        ]

        attempt = 0
        last_error: Optional[Exception] = None

        while attempt <= self.settings.max_retries:
            attempt += 1
            try:
                raw_response_text = await self._call_groq_with_timeout(
                    messages=current_messages,
                    response_schema=response_schema,
                )
                cleaned_text = self._clean_json_text(raw_response_text)
                parsed_json = json.loads(cleaned_text)
                validated_obj = response_schema.model_validate(parsed_json)
                return validated_obj

            except json.JSONDecodeError as e:
                logger.warning(f"Groq output JSON decode error (attempt {attempt}): {e}")
                last_error = GroqValidationError(f"Invalid JSON response from Groq: {e}")
            except ValidationError as e:
                logger.warning(f"Groq output schema validation failed (attempt {attempt}): {e}")
                last_error = GroqValidationError(f"Model output failed schema validation: {e}")
            except GroqPermanentAPIError:
                # Permanent errors fail immediately
                raise
            except GroqTimeoutError as e:
                logger.warning(f"Groq timeout on attempt {attempt}: {e}")
                last_error = e
            except GroqAPIError as e:
                logger.warning(f"Groq transient API error on attempt {attempt}: {e}")
                last_error = e

            if attempt <= self.settings.max_retries:
                backoff = 0.5 * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

        if isinstance(last_error, GroqError):
            raise last_error
        raise GroqAPIError(f"Failed after {self.settings.max_retries + 1} attempts: {last_error}")

    async def _call_groq_with_timeout(
        self,
        messages: list[Dict[str, str]],
        response_schema: Type[T],
    ) -> str:
        """
        Executes raw API completion request wrapped with configured timeout.
        Attempts json_schema response_format first, falling back to json_object if unsupported.
        Fails fast on permanent API errors (401, 400, 403).
        """
        json_schema = response_schema.model_json_schema()
        
        # Try provider-side json_schema format first, fallback to json_object
        response_formats = [
            {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__,
                    "schema": json_schema,
                },
            },
            {"type": "json_object"},
        ]

        last_api_exception: Optional[Exception] = None

        for resp_format in response_formats:
            try:
                response = await asyncio.wait_for(
                    self._client.chat.completions.create(
                        model=self.settings.model_name,
                        messages=messages,
                        temperature=self.settings.temperature,
                        response_format=resp_format,
                    ),
                    timeout=self.settings.timeout_seconds,
                )

                if not response.choices or not response.choices[0].message.content:
                    raise GroqAPIError("Groq returned empty response choices.")

                return response.choices[0].message.content

            except asyncio.TimeoutError:
                raise GroqTimeoutError(
                    f"Groq request timed out after {self.settings.timeout_seconds} seconds."
                )
            except PERMANENT_ERROR_CLASSES as e:
                # Permanent client error (401, 400, 403, 404). Do NOT retry.
                # If json_schema format was rejected due to 400/unsupported format, try fallback format once.
                status_code = getattr(e, "status_code", None)
                if resp_format["type"] == "json_schema" and (status_code == 400 or isinstance(e, BadRequestError)):
                    logger.info("Groq json_schema format not supported by model; falling back to json_object.")
                    continue
                raise GroqPermanentAPIError(f"Permanent Groq API error ({e.__class__.__name__}): {str(e)}")
            except (APIError, APIConnectionError, RateLimitError) as e:
                # Check status code for permanent errors
                status = getattr(e, "status_code", None)
                if status and 400 <= status < 500 and status != 429:
                    raise GroqPermanentAPIError(f"Permanent Groq API HTTP {status} error: {str(e)}")
                raise GroqAPIError(f"Transient Groq API communication error: {str(e)}")
            except Exception as e:
                if isinstance(e, (GroqTimeoutError, GroqAPIError)):
                    raise e
                raise GroqAPIError(f"Unexpected error communicating with Groq API: {str(e)}")

        if last_api_exception:
            raise last_api_exception
        raise GroqAPIError("Failed to obtain completion from Groq.")

    @staticmethod
    def _clean_json_text(text: str) -> str:
        """
        Strips markdown code block fences if returned by the model.
        """
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        return cleaned
