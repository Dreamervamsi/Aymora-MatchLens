import logging
from typing import Optional

from matchlens.ai.client import GroqClient
from matchlens.ai.config import GroqSettings
from matchlens.ai.models import ExtractedProfileUpdate
from matchlens.models.scenario import ScenarioCatalog, ScenarioResponse

logger = logging.getLogger(__name__)

SYSTEM_EXTRACTION_PROMPT = """
You are an expert matchmaking AI intake processor for MatchLens.
Your role is to analyze natural language user responses from conversational onboarding and extract structured compatibility data.

CRITICAL CONTRACT RULES:
1. EXPLICIT VS INFERRED (CONFIRMATION CONTRACT):
   - ONLY place information in `confirmed_self_attributes`, `confirmed_partner_preferences`, or `confirmed_dealbreakers` if the user explicitly and unambiguously stated it.
   - If a trait, preference, or dealbreaker is inferred, assumed, ambiguous, or stated with uncertainty, DO NOT put it in confirmed fields. Instead, create an entry in `confirmations_needed` with:
     * field_name
     * target_category ('self_attributes', 'partner_preferences', or 'dealbreakers')
     * proposed_value (the normalized value you inferred)
     * confidence (0.0 to 1.0)
     * reasoning (explanation of user's wording)
     * clarification_question (question to ask the user)
   - RULE: Any field listed in `confirmations_needed` MUST NOT be present in confirmed_self_attributes, confirmed_partner_preferences, or confirmed_dealbreakers!

2. CATEGORICAL NORMALIZATION:
   - Extracted categories MUST strictly match allowed values:
     * smoking: 'never', 'socially', 'regularly'
     * drinking: 'never', 'socially', 'regularly'
     * exercise: 'daily', 'weekly', 'rarely', 'never'
     * wants_children: 'yes', 'no', 'open', 'maybe'
     * relationship_intent: 'long_term', 'marriage', 'casual', 'friendship'
     * communication_style: 'direct', 'gentle', 'expressive', 'analytical'
     * conflict_resolution: 'discuss_immediately', 'cool_down_first', 'written_first'
     * contact_frequency: 'frequent', 'daily_check_in', 'as_needed'
   - Unstated or missing fields MUST remain null/None.

3. DISTINGUISH PERSPECTIVES & HARD DEALBREAKERS:
   - User's own traits -> confirmed_self_attributes
   - Desired partner traits -> confirmed_partner_preferences
   - Strict non-negotiables / dealbreakers -> confirmed_dealbreakers
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

    async def extract_scenario_response(
        self,
        scenario_id: str,
        user_input: str,
    ) -> ScenarioResponse:
        """
        Extracts and validates a ScenarioResponse for an active scenario assessment in the catalog.

        Args:
            scenario_id: Valid scenario identifier in ScenarioCatalog (e.g., 'conflict_resolution_01').
            user_input: User natural language response to the scenario.

        Returns:
            ScenarioResponse validated against MatchLens catalog definition.
        """
        defn = ScenarioCatalog.get_definition(scenario_id)
        if not defn:
            raise ValueError(f"Scenario ID '{scenario_id}' is unknown and not found in ScenarioCatalog.")

        scenario_system_prompt = f"""
You are an AI assessment processor for MatchLens scenario evaluation.
You are evaluating response for active scenario: '{defn.scenario_id}' ({defn.title}).
Target Dimension: {defn.target_dimension}
Allowed Choice Keys: {defn.allowed_options}

RULES:
1. normalized_preference MUST be strictly one of the allowed choice keys: {defn.allowed_options}.
2. perspective MUST be 'self_behavior' (if describing user's own choice) or 'partner_expectation' (if describing expected partner choice).
3. target_dimension MUST be exactly '{defn.target_dimension}'.
4. scenario_id MUST be exactly '{defn.scenario_id}'.
"""
        prompt = f"User Natural Language Scenario Answer:\n\"{user_input}\""

        scenario_resp = await self.client.generate_structured(
            prompt=prompt,
            system_instruction=scenario_system_prompt,
            response_schema=ScenarioResponse,
        )

        return scenario_resp
