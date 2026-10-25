import logging
from typing import Optional

from matchlens.ai.client import GroqClient
from matchlens.ai.config import GroqSettings
from matchlens.ai.models import ExtractedProfileUpdate

logger = logging.getLogger(__name__)

SYSTEM_EXTRACTION_PROMPT = """
You are an expert matchmaking AI intake processor for MatchLens.
Your role is to analyze natural language user responses from conversational onboarding and extract structured compatibility data.

CRITICAL EXTRACTION RULES:
1. DISTINGUISH PERSPECTIVES:
   - Self Characteristics -> self_attributes (e.g. "I am 28", "I don't smoke", "I value honesty")
   - Partner Expectations -> partner_preferences (e.g. "Looking for someone 25-32", "Prefer a non-smoker")
   - Hard Dealbreakers -> dealbreakers (e.g. "Never date a smoker", "Must want children")

2. PRESERVE UNCERTAINTY & MISSING DATA:
   - NEVER invent or guess facts not present in user text.
   - Leave missing/unstated fields as null/None.
   - Do NOT turn vague expressions into confirmed facts.

3. FLAG AMBIGUITIES & CONFIRMATIONS:
   - If user statement is ambiguous, add item to confirmations_needed with field_name, inferred_value, and clarification_question.
   - List any unstated fields relevant to the conversation in unanswered_fields.
   - Record any unclear statements in uncertainties.

4. SCENARIO RESPONSES:
   - If scenario assessment context is provided, parse user's normalized preference key into scenario_responses matching allowed option keys.
"""


class GroqProfileExtractor:
    """
    Service for extracting structured MatchLens profile updates from natural language onboarding responses using Groq.
    """

    def __init__(
        self,
        settings: Optional[GroqSettings] = None,
        client: Optional[GroqClient] = None,
    ):
        self.settings = settings or GroqSettings()
        self.client = client or GroqClient(settings=self.settings)

    async def extract_from_text(
        self,
        user_input: str,
        context_prompt: Optional[str] = None,
    ) -> ExtractedProfileUpdate:
        """
        Extracts structured profile updates from user natural language input.

        Args:
            user_input: The natural language string provided by the user.
            context_prompt: Optional contextual information (e.g., question asked or active scenario details).

        Returns:
            ExtractedProfileUpdate object containing validated structured extraction data.
        """
        prompt = f"User Natural Language Input:\n\"{user_input}\""
        if context_prompt:
            prompt = f"Context / Question Asked:\n{context_prompt}\n\n{prompt}"

        extracted_update = await self.client.generate_structured(
            prompt=prompt,
            system_instruction=SYSTEM_EXTRACTION_PROMPT,
            response_schema=ExtractedProfileUpdate,
        )

        return extracted_update
