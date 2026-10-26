import logging
from typing import List, Optional

from matchlens.ai.client import GroqClient
from matchlens.ai.config import GroqSettings
from matchlens.ai.models import ExtractedProfileUpdate, BatchExtractedProfile
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

SYSTEM_BATCH_EXTRACTION_PROMPT = """
You are a structured profile information extractor for MatchLens, a reciprocal relationship compatibility platform.

Your only task is to analyze a completed conversational interview and extract explicitly supported information into the provided JSON schema.

You are NOT a conversational assistant.

Rules:
1. Return exactly one valid JSON object.
2. Do not return Markdown, explanations, comments, or code fences.
3. Follow the supplied JSON schema exactly.
4. Do not add unknown fields.
5. Do not invent information that the user never stated.
6. Separate the user's personal characteristics from their ideal partner's characteristics.
7. Separate preferences from strict dealbreakers.
8. Interpret answers in the context of their corresponding interview questions.
9. Use all relevant interview answers to resolve context.
10. If answers contradict each other and the intended value cannot be determined, leave the field unknown.
11. Do not assume a missing preference means unrestricted.
12. Do not assume strict dealbreakers are enabled.
13. Do not infer gender from names, occupations, or interests.
14. Do not infer smoking, drinking, or children preferences from unrelated statements.
15. Normalize explicitly stated values into the exact enums supported by the backend:
    - smoking: 'never', 'socially', 'regularly'
    - drinking: 'never', 'socially', 'regularly'
    - exercise: 'daily', 'weekly', 'rarely', 'never'
    - wants_children: 'yes', 'no', 'open', 'maybe'
    - relationship_intent: 'long_term', 'marriage', 'casual', 'friendship'
    - communication_style: 'direct', 'gentle', 'expressive', 'analytical'
    - conflict_resolution: 'discuss_immediately', 'cool_down_first', 'written_first'
    - contact_frequency: 'frequent', 'daily_check_in', 'as_needed'
16. Never create new enum values.
17. For missing scalar fields, return null where the backend schema permits it.
18. For missing lists, follow the existing schema's missing-value semantics. Do not treat an empty list as unrestricted unless that is explicitly what the user said and the schema represents it that way.
19. Preserve explicit boolean false values.
20. Extract strict dealbreakers only when the user clearly identifies something as mandatory or non-negotiable.
21. Do not confuse a general preference with a hard eligibility constraint.
22. Return JSON that can be validated by the existing Pydantic profile models.

The output must contain three top-level objects:
- attributes
- expectations
- dealbreakers
"""


class GroqProfileExtractor:
    """
    Service for extracting structured MatchLens profile updates from natural language onboarding responses using Groq,
    with deterministic RuleProfileExtractor fallback or default.
    """

    def __init__(
        self,
        settings: Optional[GroqSettings] = None,
        client: Optional[GroqClient] = None,
        use_ai_extraction: bool = False,
    ):
        from matchlens.interview.rule_extractor import RuleProfileExtractor
        self.settings = settings or GroqSettings()
        self.use_ai_extraction = use_ai_extraction
        self.rule_extractor = RuleProfileExtractor()
        if client is not None:
            self.client = client
        else:
            try:
                self.client = GroqClient(settings=self.settings)
            except Exception as e:
                logger.info(f"GroqClient not initialized in GroqProfileExtractor ({e}).")
                self.client = None

    async def extract_from_text(
        self,
        user_input: str,
        context_prompt: Optional[str] = None,
        expected_fields: Optional[list] = None,
        permitted_values: Optional[list] = None,
    ) -> ExtractedProfileUpdate:
        """
        Extracts structured profile updates from user natural language input.
        Performs at most one focused LLM extraction call or falls back to rule-based extraction on error/timeout.
        Bypasses LLM for simple affirmative/negative/short answers.
        """
        if not user_input or not user_input.strip():
            return ExtractedProfileUpdate()

        cleaned = user_input.strip().lower()
        non_informative = {"ok", "okay", "thanks", "thank you", "sure", "got it", "hello", "hi", "hey", "yes", "no", "skip", "next"}
        if cleaned in non_informative or len(cleaned) < 2:
            logger.info(f"Bypassing LLM extraction for non-informative or direct selection response: '{user_input}'")
            return self.rule_extractor.extract_from_text(user_input, context_prompt)

        if not self.use_ai_extraction or self.client is None:
            return self.rule_extractor.extract_from_text(user_input, context_prompt)

        prompt = f"User Natural Language Input:\n\"{user_input}\""
        if context_prompt:
            prompt = f"Context / Question Asked:\n{context_prompt}\n\n{prompt}"
        if expected_fields:
            prompt += f"\nTarget Expected Fields: {expected_fields}"
        if permitted_values:
            prompt += f"\nPermitted Canonical Values: {permitted_values}"

        try:
            extracted_update = await self.client.generate_structured(
                prompt=prompt,
                system_instruction=SYSTEM_EXTRACTION_PROMPT,
                response_schema=ExtractedProfileUpdate,
            )
            return extracted_update
        except Exception as e:
            logger.warning(f"Groq LLM extraction failed or timed out ({e}); falling back to RuleProfileExtractor.")
            return self.rule_extractor.extract_from_text(user_input, context_prompt)

    async def extract_full_profile_batch(
        self,
        conversation_history: List[Any],
    ) -> ExtractedProfileUpdate:
        """
        Executes a single structured batch profile extraction over the complete interview transcript.
        If AI extraction is disabled, uninitialized, or fails/times out, falls back gracefully to RuleProfileExtractor.
        """
        # Build full transcript string in chronological order
        transcript_lines = []
        for msg in conversation_history:
            role = getattr(msg, "role", "user")
            content = getattr(msg, "content", str(msg))
            if role in ("user", "assistant"):
                transcript_lines.append(f"{role.capitalize()}: {content}")

        full_transcript = "\n".join(transcript_lines) if transcript_lines else "No conversation transcript."

        if not self.use_ai_extraction or self.client is None:
            logger.info("AI extraction disabled or client uninitialized; using RuleProfileExtractor for full batch.")
            return self.rule_extractor.extract_from_text(full_transcript)

        prompt = f"Complete Conversational Interview Transcript:\n\n{full_transcript}"

        try:
            batch_result = await self.client.generate_structured(
                prompt=prompt,
                system_instruction=SYSTEM_BATCH_EXTRACTION_PROMPT,
                response_schema=BatchExtractedProfile,
            )
            if batch_result:
                return batch_result.to_extracted_profile_update()
        except Exception as e:
            logger.warning(f"Groq batch profile extraction failed or timed out ({e}); falling back to RuleProfileExtractor.")

        return self.rule_extractor.extract_from_text(full_transcript)

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
