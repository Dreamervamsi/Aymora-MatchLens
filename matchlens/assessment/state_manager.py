import logging
import uuid
from copy import deepcopy
from typing import Dict, Optional
from matchlens.assessment.models import AssessmentState, AssessmentStage, AssessmentStatus, ScenarioDraftResponse, AssessmentProgress
from matchlens.models.scenario import ScenarioCatalog

logger = logging.getLogger(__name__)


class AssessmentStateManager:
    """
    In-memory state management for Scenario Assessment sessions.
    Supports session lifecycle and JSON serialization / deserialization.
    Returns defensive copies for public reads and validates state on save.
    """

    def __init__(self):
        self._sessions: Dict[str, AssessmentState] = {}

    def create_session(
        self,
        user_id: str,
        selected_scenario_ids: Optional[list[str]] = None,
        assessment_id: Optional[str] = None,
    ) -> AssessmentState:
        scenarios = selected_scenario_ids or ScenarioCatalog.DEFAULT_SCENARIOS
        for sid in scenarios:
            if not ScenarioCatalog.get_definition(sid):
                raise ValueError(f"Unknown scenario ID '{sid}' in selected scenarios.")

        aid = assessment_id or f"assess_{uuid.uuid4().hex[:12]}"
        
        collected = {}
        for sid in scenarios:
            defn = ScenarioCatalog.get_definition(sid)
            target_dim = defn.target_dimension if defn else "communication_preferences"
            collected[sid] = ScenarioDraftResponse(
                scenario_id=sid,
                target_dimension=target_dim,
            )

        progress = AssessmentProgress(
            current_scenario_index=0,
            total_scenarios=len(scenarios),
            completed_scenario_ids=[],
            current_stage=AssessmentStage.SELF_BEHAVIOR,
            percentage=0.0,
        )

        state = AssessmentState(
            assessment_id=aid,
            user_id=user_id,
            selected_scenario_ids=scenarios,
            current_scenario_index=0,
            current_stage=AssessmentStage.SELF_BEHAVIOR,
            collected_responses=collected,
            unresolved_clarification=None,
            status=AssessmentStatus.ACTIVE,
            progress=progress,
        )

        self.save_session(state)
        return self.get_session(aid)  # type: ignore

    def get_session(self, assessment_id: str) -> Optional[AssessmentState]:
        state = self._sessions.get(assessment_id)
        return deepcopy(state) if state else None

    def save_session(self, state: AssessmentState) -> None:
        validated_state = AssessmentState.model_validate(state.model_dump())
        self._sessions[state.assessment_id] = deepcopy(validated_state)

    def delete_session(self, assessment_id: str) -> bool:
        if assessment_id in self._sessions:
            del self._sessions[assessment_id]
            return True
        return False

    def serialize_state(self, assessment_id: str) -> str:
        state = self.get_session(assessment_id)
        if not state:
            raise ValueError(f"Assessment ID '{assessment_id}' not found.")
        return state.model_dump_json()

    def deserialize_state(self, json_data: str) -> AssessmentState:
        state = AssessmentState.model_validate_json(json_data)
        self.save_session(state)
        return self.get_session(state.assessment_id)  # type: ignore
