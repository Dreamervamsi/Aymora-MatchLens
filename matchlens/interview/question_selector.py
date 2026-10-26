import logging
from typing import Optional
from matchlens.ai.client import GroqClient
from matchlens.ai.config import GroqSettings
from matchlens.interview.models import InterviewState, InterviewTopic
from matchlens.interview.question_bank import get_bank_question, get_bank_definition, QuestionDefinition

logger = logging.getLogger(__name__)


class HybridQuestionSelector:
    """
    100% deterministic question selector that picks target topic questions from the static question pool.
    Zero LLM calls are executed for question generation.
    """

    def __init__(
        self,
        settings: Optional[GroqSettings] = None,
        client: Optional[GroqClient] = None,
    ):
        self.settings = settings or GroqSettings()
        self.client = client

    async def select_and_generate_question(
        self,
        state: InterviewState,
        target_topic: InterviewTopic,
        missing_field_key: Optional[str] = None,
        clarification_prompt: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Selects the next question for the user deterministically from the question bank.

        Args:
            state: Current InterviewState
            target_topic: Topic selected by Python control logic
            missing_field_key: Optional specific missing attribute/preference
            clarification_prompt: Optional prompt text if clarifying an ambiguous inference

        Returns:
            Tuple of (question_id, question_text)
        """
        if clarification_prompt:
            q_id = f"clarification.{missing_field_key or 'ambiguity'}"
            return q_id, clarification_prompt

        defn = get_bank_definition(target_topic, missing_field_key)
        return defn.question_id, defn.question_text

