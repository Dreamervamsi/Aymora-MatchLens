"""
Scenario assessment endpoints router.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from matchlens.api.dependencies import get_assessment_orchestrator, get_profile_repository
from matchlens.api.repository import ProfileRepository
from matchlens.api.schemas import (
    AssessmentCorrectionRequest,
    AssessmentStateResponse,
    AssessmentTurnRequest,
    AssessmentTurnResponse,
    StartAssessmentRequest,
)
from matchlens.assessment.integration import attach_scenario_responses
from matchlens.assessment.orchestrator import ScenarioAssessmentOrchestrator
from matchlens.models.profile import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessment", tags=["Assessment"])


@router.post("/start", response_model=AssessmentTurnResponse, status_code=status.HTTP_201_CREATED)
async def start_assessment(
    payload: StartAssessmentRequest,
    orchestrator: ScenarioAssessmentOrchestrator = Depends(get_assessment_orchestrator),
    repository: ProfileRepository = Depends(get_profile_repository),
) -> AssessmentTurnResponse:
    """
    Initializes a scenario-based relationship assessment.
    Verifies that the user has a confirmed profile in the repository first.
    """
    user_profile = repository.get_profile(payload.user_id)
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{payload.user_id}' does not have a confirmed profile. Complete interview profile confirmation first.",
        )

    try:
        turn_result = orchestrator.start_assessment(
            user_id=payload.user_id,
            selected_scenario_ids=payload.selected_scenario_ids,
            assessment_id=payload.assessment_id,
        )
        return AssessmentTurnResponse(
            assessment_id=turn_result.assessment_id,
            status=turn_result.status,
            current_stage=turn_result.current_stage,
            current_scenario_id=turn_result.current_scenario_id,
            scenario_definition=turn_result.scenario_definition,
            prompt_text=turn_result.prompt_text,
            allowed_options=turn_result.allowed_options,
            unresolved_clarification=turn_result.unresolved_clarification,
            progress=turn_result.progress,
            summary_data=turn_result.summary_data,
        )
    except Exception as e:
        logger.error(f"Failed to start assessment: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{assessment_id}/turn", response_model=AssessmentTurnResponse)
async def submit_assessment_turn(
    assessment_id: str,
    payload: AssessmentTurnRequest,
    orchestrator: ScenarioAssessmentOrchestrator = Depends(get_assessment_orchestrator),
) -> AssessmentTurnResponse:
    """
    Submits user response for the active scenario stage.
    """
    try:
        turn_result = await orchestrator.submit_response(
            assessment_id=assessment_id,
            user_response=payload.user_response,
        )
        return AssessmentTurnResponse(
            assessment_id=turn_result.assessment_id,
            status=turn_result.status,
            current_stage=turn_result.current_stage,
            current_scenario_id=turn_result.current_scenario_id,
            scenario_definition=turn_result.scenario_definition,
            prompt_text=turn_result.prompt_text,
            allowed_options=turn_result.allowed_options,
            unresolved_clarification=turn_result.unresolved_clarification,
            progress=turn_result.progress,
            summary_data=turn_result.summary_data,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "unknown assessment" in str(ve).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Error in assessment turn: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during assessment turn.")


@router.post("/{assessment_id}/correct", response_model=AssessmentTurnResponse)
async def correct_assessment_response(
    assessment_id: str,
    payload: AssessmentCorrectionRequest,
    orchestrator: ScenarioAssessmentOrchestrator = Depends(get_assessment_orchestrator),
) -> AssessmentTurnResponse:
    """
    Corrects a previously provided self or partner scenario response during review.
    """
    try:
        turn_result = orchestrator.correct_response(
            assessment_id=assessment_id,
            scenario_id=payload.scenario_id,
            target=payload.target,
            new_value=payload.new_value,
        )
        return AssessmentTurnResponse(
            assessment_id=turn_result.assessment_id,
            status=turn_result.status,
            current_stage=turn_result.current_stage,
            current_scenario_id=turn_result.current_scenario_id,
            scenario_definition=turn_result.scenario_definition,
            prompt_text=turn_result.prompt_text,
            allowed_options=turn_result.allowed_options,
            unresolved_clarification=turn_result.unresolved_clarification,
            progress=turn_result.progress,
            summary_data=turn_result.summary_data,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "unknown assessment" in str(ve).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )


@router.get("/{assessment_id}", response_model=AssessmentStateResponse)
async def get_assessment_state(
    assessment_id: str,
    orchestrator: ScenarioAssessmentOrchestrator = Depends(get_assessment_orchestrator),
) -> AssessmentStateResponse:
    """
    Retrieves status and progress for an active or completed assessment session.
    """
    try:
        state = orchestrator.get_assessment_state(assessment_id)
        return AssessmentStateResponse(
            assessment_id=state.assessment_id,
            user_id=state.user_id,
            status=state.status,
            current_stage=state.current_stage,
            selected_scenario_ids=state.selected_scenario_ids,
            progress=state.progress,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.post("/{assessment_id}/confirm", response_model=UserProfile)
async def confirm_assessment(
    assessment_id: str,
    orchestrator: ScenarioAssessmentOrchestrator = Depends(get_assessment_orchestrator),
    repository: ProfileRepository = Depends(get_profile_repository),
) -> UserProfile:
    """
    Confirms assessment responses and attaches canonical ScenarioResponse objects to the user profile.
    """
    try:
        state = orchestrator.get_assessment_state(assessment_id)
        user_profile = repository.get_profile(state.user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{state.user_id}' does not have a confirmed profile in the repository.",
            )

        # Confirm assessment status
        orchestrator.confirm_assessment(assessment_id)

        # Retrieve completed canonical scenario responses
        scenario_responses = orchestrator.get_completed_responses(assessment_id)

        # Attach to user profile using integration utility
        updated_profile = attach_scenario_responses(
            profile=user_profile,
            new_responses=scenario_responses,
            replace_existing=True,
        )

        # Save updated profile to repository
        saved = repository.update_profile(updated_profile)
        return saved
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error confirming assessment: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to confirm assessment.")
