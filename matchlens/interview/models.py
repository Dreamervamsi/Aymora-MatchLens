from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

from matchlens.ai.models import ConfirmationPrompt, ExtractedProfileUpdate
from matchlens.models.profile import UserProfile


class InterviewStatus(str, Enum):
    ACTIVE = "active"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    READY_FOR_REVIEW = "ready_for_review"
    COMPLETED = "completed"


class InterviewTopic(str, Enum):
    BASIC_AND_INTENTION = "basic_and_intention"
    CORE_VALUES = "core_values"
    LIFESTYLE = "lifestyle"
    COMMUNICATION = "communication"
    PARTNER_EXPECTATIONS = "partner_expectations"
    DEALBREAKERS = "dealbreakers"


TOPIC_ORDER: List[InterviewTopic] = [
    InterviewTopic.BASIC_AND_INTENTION,
    InterviewTopic.CORE_VALUES,
    InterviewTopic.LIFESTYLE,
    InterviewTopic.COMMUNICATION,
    InterviewTopic.PARTNER_EXPECTATIONS,
    InterviewTopic.DEALBREAKERS,
]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PendingConfirmation(BaseModel):
    field_name: str
    target_category: Literal["self_attributes", "partner_preferences", "dealbreakers"]
    proposed_value: Any
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    reasoning: str
    clarification_question: str

    @classmethod
    def from_confirmation_prompt(cls, prompt: ConfirmationPrompt) -> "PendingConfirmation":
        return cls(
            field_name=prompt.field_name,
            target_category=prompt.target_category,
            proposed_value=prompt.proposed_value,
            confidence=prompt.confidence,
            reasoning=prompt.reasoning,
            clarification_question=prompt.clarification_question,
        )


class InterviewProgress(BaseModel):
    completed_topics: List[InterviewTopic] = Field(default_factory=list)
    current_topic: InterviewTopic = InterviewTopic.BASIC_AND_INTENTION
    percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    essential_fields_satisfied: bool = False


class InterviewState(BaseModel):
    session_id: str
    user_id: str
    status: InterviewStatus = InterviewStatus.ACTIVE
    current_topic: InterviewTopic = InterviewTopic.BASIC_AND_INTENTION
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    draft_profile: UserProfile
    pending_confirmations: List[PendingConfirmation] = Field(default_factory=list)
    unanswered_fields: List[str] = Field(default_factory=list)
    previously_asked_question_ids: List[str] = Field(default_factory=list)
    topic_turn_counts: Dict[str, int] = Field(default_factory=dict)
    turn_count: int = 0
    progress: InterviewProgress = Field(default_factory=InterviewProgress)


class InterviewTurnResult(BaseModel):
    session_id: str
    assistant_message: str
    interview_status: InterviewStatus
    current_topic: InterviewTopic
    progress: InterviewProgress
    newly_extracted_fields: List[str] = Field(default_factory=list)
    pending_confirmations: List[PendingConfirmation] = Field(default_factory=list)
    missing_essential_fields: List[str] = Field(default_factory=list)
    is_ready_for_review: bool = False
