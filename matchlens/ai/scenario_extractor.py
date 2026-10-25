import logging
from typing import Optional, Tuple
from pydantic import BaseModel, Field

from matchlens.ai.client import GroqClient
from matchlens.ai.config import GroqSettings
from matchlens.models.scenario import ScenarioCatalog, ScenarioDefinition

logger = logging.getLogger(__name__)


class ScenarioInterpretationResult(BaseModel):
    """
    Structured extraction result mapping user natural language input to allowed scenario options.
    """
    matched_option: Optional[str] = Field(
        default=None,
        description="Matched allowed option key, or None if input cannot be reliably mapped."
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in AI option mapping."
    )
    is_ambiguous: bool = Field(
        default=False,
        description="True if input is qualified, uncertain, or matches multiple options with similar likelihood."
    )
    reasoning: str = Field(
        default="",
        description="Explanation of interpretation."
    )
    clarification_prompt: str = Field(
        default="",
        description="Question to ask user if clarification is needed."
    )


EXTRACTION_SYSTEM_PROMPT = """
You are an expert matchmaking AI intake processor for MatchLens scenario evaluation.
Your task is to analyze user natural language responses to hypothetical scenario questions and map them to one of the predefined allowed options.

CRITICAL RULES:
1. `matched_option` MUST be strictly one of the specified allowed options, or null if uncertain/unmatched.
2. `confidence` must be between 0.0 and 1.0.
3. If the user's response is ambiguous, qualified ("maybe", "depends", "it depends"), hesitant, or could match multiple options equally, set `is_ambiguous=True`, provide `confidence` < 0.7, set `matched_option` to the most likely option, and write a clear `clarification_prompt`.
4. If the user's response clearly matches one allowed option without hesitation, set `is_ambiguous=False`, set high `confidence` (>= 0.85), and set `matched_option`.
5. NEVER invent options outside the provided allowed options list.
"""


class GroqScenarioExtractor:
    """
    Extractor and normalizer for scenario-based responses using exact matching or Groq AI interpretation.
    """

    def __init__(
        self,
        settings: Optional[GroqSettings] = None,
        client: Optional[GroqClient] = None,
    ):
        self.settings = settings or GroqSettings()
        if client is not None:
            self.client = client
        else:
            try:
                self.client = GroqClient(settings=self.settings)
            except Exception as e:
                logger.info(f"GroqClient not initialized in GroqScenarioExtractor ({e}).")
                self.client = None

    def direct_validate_option(self, scenario_id: str, input_text: str) -> Optional[str]:
        """
        Directly validates structured choice input against ScenarioCatalog allowed_options.
        Returns normalized option key string if matched, else None.
        """
        defn = ScenarioCatalog.get_definition(scenario_id)
        if not defn:
            return None

        cleaned = input_text.strip().lower()

        # Exact match check
        for opt in defn.allowed_options:
            if cleaned == opt.lower():
                return opt

        # 1-based index selection check (e.g., '1', '2')
        if cleaned.isdigit():
            idx = int(cleaned) - 1
            if 0 <= idx < len(defn.allowed_options):
                return defn.allowed_options[idx]

        # Check against option descriptions or common aliases if available
        if defn.option_descriptions:
            for opt_key, desc in defn.option_descriptions.items():
                if cleaned in desc.lower():
                    return opt_key

        return None

    async def normalize_response(
        self,
        scenario_id: str,
        stage_description: str,
        user_input: str,
    ) -> ScenarioInterpretationResult:
        """
        Normalizes a user response (structured or natural language) for a scenario stage.
        Falls back gracefully if Groq client is not available.
        """
        defn = ScenarioCatalog.get_definition(scenario_id)
        if not defn:
            raise ValueError(f"Unknown scenario ID '{scenario_id}'.")

        # First, attempt direct validation
        direct_match = self.direct_validate_option(scenario_id, user_input)
        if direct_match:
            return ScenarioInterpretationResult(
                matched_option=direct_match,
                confidence=1.0,
                is_ambiguous=False,
                reasoning=f"Direct match to allowed option '{direct_match}'.",
            )

        # Fallback if AI client is missing/uninitialized
        if self.client is None:
            logger.warning(f"Groq client uninitialized; unable to perform AI normalization for '{user_input}'.")
            return ScenarioInterpretationResult(
                matched_option=None,
                confidence=0.0,
                is_ambiguous=True,
                reasoning="AI service unavailable for free-text interpretation.",
                clarification_prompt=f"Please select one of the allowed options: {', '.join(defn.allowed_options)}.",
            )

        # Build AI interpretation prompt
        prompt = f"""
Scenario Title: {defn.title}
Scenario Description: {defn.description or ''}
Target Dimension: {defn.target_dimension}
Current Stage / Prompt Context: {stage_description}
Allowed Options: {defn.allowed_options}
Option Descriptions: {defn.option_descriptions or {}}

User Input Text:
"{user_input}"
"""

        try:
            result = await self.client.generate_structured(
                prompt=prompt,
                system_instruction=EXTRACTION_SYSTEM_PROMPT,
                response_schema=ScenarioInterpretationResult,
            )
            return result
        except Exception as e:
            logger.error(f"Groq scenario extraction failed for '{scenario_id}': {e}")
            return ScenarioInterpretationResult(
                matched_option=None,
                confidence=0.0,
                is_ambiguous=True,
                reasoning=f"AI extraction encountered an error ({type(e).__name__}).",
                clarification_prompt=f"I couldn't interpret your answer automatically. Please select one of: {', '.join(defn.allowed_options)}.",
            )
