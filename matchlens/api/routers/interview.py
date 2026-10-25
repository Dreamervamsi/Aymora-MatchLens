"""
Interview endpoints router.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from matchlens.api.dependencies import get_interview_orchestrator, get_profile_repository
from matchlens.api.repository import ProfileRepository
from matchlens.api.schemas import (
    InterviewStateResponse,
    InterviewTurnRequest,
    InterviewTurnResponse,
    StartInterviewRequest,
)
from matchlens.interview.orchestrator import InterviewOrchestrator
from matchlens.models.profile import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview", tags=["Interview"])


@router.post("/start", response_model=InterviewTurnResponse, status_code=status.HTTP_201_CREATED)
async def start_interview(
    payload: StartInterviewRequest,
    orchestrator: InterviewOrchestrator = Depends(get_interview_orchestrator),
) -> InterviewTurnResponse:
    """
    Initializes a new conversational onboarding interview session.
    """
    try:
        state, opening_msg = orchestrator.start_interview(
            user_id=payload.user_id,
            session_id=payload.session_id,
        )
        return InterviewTurnResponse(
            session_id=state.session_id,
            assistant_message=opening_msg,
            interview_status=state.status,
            current_topic=state.current_topic,
            progress=state.progress,
            newly_extracted_fields=[],
            pending_confirmations=state.pending_confirmations,
            missing_essential_fields=orchestrator._get_missing_essential_fields(state),
            is_ready_for_review=False,
        )
    except Exception as e:
        logger.error(f"Failed to start interview: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{session_id}/turn", response_model=InterviewTurnResponse)
async def process_interview_turn(
    session_id: str,
    payload: InterviewTurnRequest,
    orchestrator: InterviewOrchestrator = Depends(get_interview_orchestrator),
) -> InterviewTurnResponse:
    """
    Processes a single conversational turn in an ongoing interview session.
    """
    try:
        turn_result = await orchestrator.process_turn(
            session_id=session_id,
            user_message=payload.user_message,
        )
        return InterviewTurnResponse(
            session_id=turn_result.session_id,
            assistant_message=turn_result.assistant_message,
            interview_status=turn_result.interview_status,
            current_topic=turn_result.current_topic,
            progress=turn_result.progress,
            newly_extracted_fields=turn_result.newly_extracted_fields,
            pending_confirmations=turn_result.pending_confirmations,
            missing_essential_fields=turn_result.missing_essential_fields,
            is_ready_for_review=turn_result.is_ready_for_review,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND if "not found" in str(ve).lower() else status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error in interview turn: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while processing the turn.")


@router.get("/{session_id}", response_model=InterviewStateResponse)
async def get_interview_state(
    session_id: str,
    orchestrator: InterviewOrchestrator = Depends(get_interview_orchestrator),
) -> InterviewStateResponse:
    """
    Retrieves current state and draft profile for an interview session.
    """
    state = orchestrator.state_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Interview session '{session_id}' not found.")

    return InterviewStateResponse(
        session_id=state.session_id,
        user_id=state.user_id,
        status=state.status,
        current_topic=state.current_topic,
        turn_count=state.turn_count,
        progress=state.progress,
        pending_confirmations=state.pending_confirmations,
        draft_profile=state.draft_profile,
    )


@router.post("/{session_id}/confirm", response_model=UserProfile)
async def confirm_interview_profile(
    session_id: str,
    orchestrator: InterviewOrchestrator = Depends(get_interview_orchestrator),
    repository: ProfileRepository = Depends(get_profile_repository),
) -> UserProfile:
    """
    Confirms and finalizes the draft interview profile, saving it to the profile repository.
    Preserves existing confirmed scenario assessments if an existing profile is being reconfirmed/updated.
    """
    state = orchestrator.state_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Interview session '{session_id}' not found.")

    existing_profile = repository.get_profile(state.user_id)

    try:
        confirmed_profile = orchestrator.confirm_draft_profile(session_id)

        # Fix P1: Preserve existing confirmed scenario responses if user already had a stored profile
        if existing_profile and existing_profile.scenarios:
            # Merge existing scenario responses into confirmed draft profile
            existing_scenarios = existing_profile.scenarios
            scenarios_map = {s.scenario_id: s for s in existing_scenarios}
            # Add any draft scenarios
            for s in confirmed_profile.scenarios:
                scenarios_map[s.scenario_id] = s
            confirmed_profile.scenarios = list(scenarios_map.values())

        saved = repository.save_profile(confirmed_profile, overwrite=True if existing_profile else False)
        return saved
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error confirming interview profile: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to confirm interview profile.")
