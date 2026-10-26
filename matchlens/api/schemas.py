"""
API request and response Pydantic models.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from matchlens.interview.models import ChatMessage, InterviewStatus, InterviewTopic, InterviewProgress, PendingConfirmation
from matchlens.assessment.models import AssessmentStatus, AssessmentStage, AssessmentProgress, ClarificationRequest
from matchlens.models.scenario import ScenarioDefinition, ScenarioResponse
from matchlens.models.profile import UserProfile


# --- General / Health Schemas ---

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "v1"


# --- Interview Schemas ---

class StartInterviewRequest(BaseModel):
    user_id: str = Field(description="Unique identifier for the user starting the interview")
    session_id: Optional[str] = Field(default=None, description="Optional custom session identifier")


class InterviewTurnRequest(BaseModel):
    user_message: str = Field(description="User message for the interview turn")


class InterviewTurnResponse(BaseModel):
    session_id: str
    assistant_message: str
    interview_status: InterviewStatus
    current_topic: InterviewTopic
    progress: InterviewProgress
    newly_extracted_fields: List[str] = Field(default_factory=list)
    pending_confirmations: List[PendingConfirmation] = Field(default_factory=list)
    missing_essential_fields: List[str] = Field(default_factory=list)
    is_ready_for_review: bool = False


class InterviewStateResponse(BaseModel):
    session_id: str
    user_id: str
    status: InterviewStatus
    current_topic: InterviewTopic
    turn_count: int
    progress: InterviewProgress
    pending_confirmations: List[PendingConfirmation] = Field(default_factory=list)
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    draft_profile: UserProfile


# --- Assessment Schemas ---

class StartAssessmentRequest(BaseModel):
    user_id: str = Field(description="Unique identifier for the user starting the assessment")
    selected_scenario_ids: Optional[List[str]] = Field(default=None, description="List of scenario IDs to include")
    assessment_id: Optional[str] = Field(default=None, description="Optional custom assessment identifier")


class AssessmentTurnRequest(BaseModel):
    user_response: str = Field(description="User input for the active scenario stage or review command")


class AssessmentCorrectionRequest(BaseModel):
    scenario_id: str = Field(description="Target scenario ID to correct")
    target: str = Field(description="'self_behavior' or 'partner_expectation'")
    new_value: str = Field(description="Corrected option string")


class AssessmentTurnResponse(BaseModel):
    assessment_id: str
    status: AssessmentStatus
    current_stage: AssessmentStage
    current_scenario_id: Optional[str] = None
    scenario_definition: Optional[ScenarioDefinition] = None
    prompt_text: str
    allowed_options: List[str] = Field(default_factory=list)
    unresolved_clarification: Optional[ClarificationRequest] = None
    progress: AssessmentProgress
    summary_data: Optional[Dict[str, Dict[str, Optional[str]]]] = None


from matchlens.models.scoring import MatchResult


class AssessmentStateResponse(BaseModel):
    assessment_id: str
    user_id: str
    status: AssessmentStatus
    current_stage: AssessmentStage
    selected_scenario_ids: List[str]
    current_scenario_id: Optional[str] = None
    scenario_definition: Optional[ScenarioDefinition] = None
    prompt_text: Optional[str] = None
    allowed_options: List[str] = Field(default_factory=list)
    unresolved_clarification: Optional[ClarificationRequest] = None
    progress: AssessmentProgress
    summary_data: Optional[Dict[str, Dict[str, Optional[str]]]] = None


# --- Matching Schemas ---

class MatchRecommendationResponse(BaseModel):
    requesting_user_id: str
    top_matches: List[MatchResult]
    ranking_metadata: Dict[str, int]
