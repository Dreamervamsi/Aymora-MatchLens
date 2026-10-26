import logging
from typing import Optional
from pydantic import BaseModel, Field

from matchlens.ai.client import GroqClient
from matchlens.ai.config import GroqSettings
from matchlens.interview.models import InterviewState, InterviewTopic
from matchlens.interview.question_bank import get_bank_question

logger = logging.getLogger(__name__)


class GeneratedQuestionSchema(BaseModel):
    question_text: str = Field(description="Natural, context-aware question addressing target topic and missing information")
    question_id: str = Field(description="Unique string identifier or field key for tracking asked questions")


SYSTEM_QUESTION_GENERATOR_PROMPT = """
You are a warm, perceptive matchmaking AI interviewer for MatchLens.
Your objective is to generate ONE focused, natural follow-up question for the user during onboarding.

RULES:
1. Focus strictly on the target interview topic and specific missing fields requested.
2. Ask ONE concise, friendly question per turn.
3. Do NOT repeat questions that have already been asked or answered.
4. Keep question phrasing natural, polite, and under 25 words.
5. Respect self attributes vs partner expectations: do NOT confuse the user's own trait with what they want in a partner.
"""


class HybridQuestionSelector:
    """
    Selects target topic and missing fields using Python rules,
    generates contextual wording via Groq AI, and falls back to deterministic question bank on failure.
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
                logger.info(f"GroqClient not initialized in HybridQuestionSelector ({e}); defaulting to question bank.")
                self.client = None

    async def select_and_generate_question(
        self,
        state: InterviewState,
        target_topic: InterviewTopic,
        missing_field_key: Optional[str] = None,
        clarification_prompt: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Generates the next question for the user.

        Args:
            state: Current InterviewState
            target_topic: Topic selected by Python control logic
            missing_field_key: Optional specific missing attribute/preference
            clarification_prompt: Optional prompt text if clarifying an ambiguous inference

        Returns:
            Tuple of (question_id, question_text)
        """
        # If there is an active clarification required, use that directly
        if clarification_prompt:
            q_id = f"clarification.{missing_field_key or 'ambiguity'}"
            return q_id, clarification_prompt

        # Obtain deterministic fallback first
        fallback_id, fallback_text = get_bank_question(target_topic, missing_field_key)

        # Fast-path: If fallback question exists and client is not required or we want fast template selection,
        # use deterministic question bank directly to reduce serial Groq LLM latency.
        if fallback_id and fallback_text and not fallback_id.startswith("default."):
            return fallback_id, fallback_text

        if self.client is None:
            return fallback_id, fallback_text

        # Build prompt for Groq
        recent_history = [
            f"{m.role.capitalize()}: {m.content}"
            for m in state.conversation_history[-4:]
        ]
        history_str = "\n".join(recent_history) if recent_history else "No prior history."

        prompt = f"""
Current Interview Topic: {target_topic.value}
Target Missing Field/Trait: {missing_field_key or 'General topic exploration'}
Previously Asked Question IDs: {state.previously_asked_question_ids}

Recent Conversation History:
{history_str}

Standard Fallback Reference Question:
"{fallback_text}"

Generate ONE natural, concise follow-up question.
"""

        try:
            res = await self.client.generate_structured(
                prompt=prompt,
                system_instruction=SYSTEM_QUESTION_GENERATOR_PROMPT,
                response_schema=GeneratedQuestionSchema,
            )
            # Validate generated question text is non-empty
            if res and res.question_text and res.question_text.strip():
                question_id = res.question_id or fallback_id
                return question_id, res.question_text.strip()

        except Exception as e:
            logger.warning(f"Groq question generation failed ({e}); falling back to deterministic question bank.")

        return fallback_id, fallback_text
