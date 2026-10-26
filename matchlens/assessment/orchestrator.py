import logging
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from matchlens.ai.scenario_extractor import GroqScenarioExtractor
from matchlens.assessment.models import (
    AssessmentProgress,
    AssessmentStage,
    AssessmentState,
    AssessmentStatus,
    AssessmentTurnResult,
    ClarificationRequest,
    ScenarioDraftResponse,
)
from matchlens.assessment.state_manager import AssessmentStateManager
from matchlens.models.scenario import ScenarioCatalog, ScenarioDefinition, ScenarioResponse

logger = logging.getLogger(__name__)


class ScenarioAssessmentOrchestrator:
    """
    Orchestrates scenario-based relationship assessment flows.
    Manages stage progression, independent two-part response collection,
    AI normalization, review corrections, and canonical ScenarioResponse generation.
    """

    def __init__(
        self,
        state_manager: Optional[AssessmentStateManager] = None,
        extractor: Optional[GroqScenarioExtractor] = None,
    ):
        self.state_manager = state_manager or AssessmentStateManager()
        self.extractor = extractor or GroqScenarioExtractor()

    def start_assessment(
        self,
        user_id: str,
        selected_scenario_ids: Optional[List[str]] = None,
        assessment_id: Optional[str] = None,
    ) -> AssessmentTurnResult:
        """
        Initializes a new assessment session and returns the initial prompt.
        """
        state = self.state_manager.create_session(
            user_id=user_id,
            selected_scenario_ids=selected_scenario_ids,
            assessment_id=assessment_id,
        )
        return self._build_turn_result(state)

    async def submit_response(
        self,
        assessment_id: str,
        user_response: str,
    ) -> AssessmentTurnResult:
        """
        Processes user input for the current scenario stage.
        Uses atomic state updates so failures do not corrupt state.
        """
        state = self.state_manager.get_session(assessment_id)
        if not state:
            raise ValueError(f"Unknown assessment ID '{assessment_id}'.")

        if state.status == AssessmentStatus.COMPLETED:
            return self._build_turn_result(
                state,
                override_prompt="Assessment is already completed and confirmed.",
            )

        cleaned_input = (user_response or "").strip()
        if not cleaned_input:
            return self._build_turn_result(
                state,
                override_prompt="Please provide a valid, non-empty response.",
            )

        # Work on a deepcopy for atomic updates
        working = deepcopy(state)
        working.updated_at = datetime.now(timezone.utc)

        # 1. Handle clarification resolution if active
        if working.unresolved_clarification:
            resolved_opt = self.extractor.direct_validate_option(
                working.unresolved_clarification.scenario_id,
                cleaned_input,
            )
            # Check for affirmative confirmation (e.g., 'yes', 'yep', 'correct')
            if not resolved_opt and cleaned_input.lower() in ["yes", "yep", "yeah", "correct", "sure", "true"]:
                resolved_opt = working.unresolved_clarification.proposed_option

            if resolved_opt:
                # Clarification resolved! Apply option
                clar = working.unresolved_clarification
                draft = working.collected_responses[clar.scenario_id]
                if clar.stage == AssessmentStage.SELF_BEHAVIOR:
                    draft.self_response = resolved_opt
                    draft.self_raw_input = clar.raw_input
                    working.current_stage = AssessmentStage.PARTNER_EXPECTATION
                elif clar.stage == AssessmentStage.PARTNER_EXPECTATION:
                    draft.partner_expectation = resolved_opt
                    draft.partner_raw_input = clar.raw_input
                    self._advance_to_next_scenario_or_review(working)

                working.unresolved_clarification = None
                self._update_progress(working)
                self.state_manager.save_session(working)
                return self._build_turn_result(working)
            else:
                # Still unresolved
                defn = ScenarioCatalog.get_definition(working.unresolved_clarification.scenario_id)
                opts_str = ", ".join(defn.allowed_options) if defn else ""
                reask_prompt = (
                    f"I couldn't confirm that choice. Please select one of the allowed options: {opts_str}"
                )
                return self._build_turn_result(working, override_prompt=reask_prompt)

        # 2. Handle standard active assessment turn
        if working.status == AssessmentStatus.ACTIVE:
            curr_sid = working.selected_scenario_ids[working.current_scenario_index]
            defn = ScenarioCatalog.get_definition(curr_sid)
            if not defn:
                raise ValueError(f"Unknown scenario ID '{curr_sid}' in state.")

            draft = working.collected_responses[curr_sid]
            stage_desc = (
                f"Self behavior response for '{defn.title}'"
                if working.current_stage == AssessmentStage.SELF_BEHAVIOR
                else f"Partner expectation response for '{defn.title}'"
            )

            # Direct validation check first
            direct_opt = self.extractor.direct_validate_option(curr_sid, cleaned_input)
            if direct_opt:
                if working.current_stage == AssessmentStage.SELF_BEHAVIOR:
                    draft.self_response = direct_opt
                    draft.self_raw_input = cleaned_input
                    working.current_stage = AssessmentStage.PARTNER_EXPECTATION
                elif working.current_stage == AssessmentStage.PARTNER_EXPECTATION:
                    draft.partner_expectation = direct_opt
                    draft.partner_raw_input = cleaned_input
                    self._advance_to_next_scenario_or_review(working)

                self._update_progress(working)
                self.state_manager.save_session(working)
                return self._build_turn_result(working)

            # AI Normalization for natural language input
            interpretation = await self.extractor.normalize_response(
                scenario_id=curr_sid,
                stage_description=stage_desc,
                user_input=cleaned_input,
            )

            if interpretation.is_ambiguous or interpretation.confidence < 0.7 or not interpretation.matched_option:
                proposed = interpretation.matched_option or defn.allowed_options[0]
                clar_prompt = (
                    interpretation.clarification_prompt
                    or f"Did you mean '{proposed}'? (Allowed options: {', '.join(defn.allowed_options)})"
                )
                working.unresolved_clarification = ClarificationRequest(
                    scenario_id=curr_sid,
                    stage=working.current_stage,
                    raw_input=cleaned_input,
                    proposed_option=proposed,
                    confidence=interpretation.confidence,
                    reasoning=interpretation.reasoning,
                    clarification_prompt=clar_prompt,
                )
                self.state_manager.save_session(working)
                return self._build_turn_result(working)

            # Confident AI match
            matched_opt = interpretation.matched_option
            if working.current_stage == AssessmentStage.SELF_BEHAVIOR:
                draft.self_response = matched_opt
                draft.self_raw_input = cleaned_input
                working.current_stage = AssessmentStage.PARTNER_EXPECTATION
            elif working.current_stage == AssessmentStage.PARTNER_EXPECTATION:
                draft.partner_expectation = matched_opt
                draft.partner_raw_input = cleaned_input
                self._advance_to_next_scenario_or_review(working)

            self._update_progress(working)
            self.state_manager.save_session(working)
            return self._build_turn_result(working)

        # 3. If in READY_FOR_REVIEW state
        if working.status == AssessmentStatus.READY_FOR_REVIEW:
            if cleaned_input.lower() in ["confirm", "yes", "looks good", "submit", "done", "ok"]:
                return self._build_turn_result(
                    working,
                    override_prompt="All scenarios answered! Please click the 'Confirm & Finalize' button in the UI to save your responses to your profile.",
                )
            else:
                return self._build_turn_result(
                    working,
                    override_prompt="You are in review stage. Please review your responses and click 'Confirm & Finalize' to save to profile.",
                )

        return self._build_turn_result(working)

    def correct_response(
        self,
        assessment_id: str,
        scenario_id: str,
        target: str,  # "self_behavior" or "partner_expectation"
        new_value: str,
    ) -> AssessmentTurnResult:
        """
        Allows independent correction of self_behavior or partner_expectation during review or active states.
        Revalidates corrected option against ScenarioCatalog.
        """
        state = self.state_manager.get_session(assessment_id)
        if not state:
            raise ValueError(f"Unknown assessment ID '{assessment_id}'.")

        if scenario_id not in state.collected_responses:
            raise ValueError(f"Scenario ID '{scenario_id}' was not part of this assessment.")

        defn = ScenarioCatalog.get_definition(scenario_id)
        if not defn:
            raise ValueError(f"Unknown scenario ID '{scenario_id}'.")

        norm_opt = self.extractor.direct_validate_option(scenario_id, new_value)
        if not norm_opt:
            raise ValueError(
                f"Invalid option '{new_value}' for scenario '{scenario_id}'. Allowed options: {defn.allowed_options}."
            )

        working = deepcopy(state)
        working.updated_at = datetime.now(timezone.utc)
        draft = working.collected_responses[scenario_id]

        if target == "self_behavior":
            draft.self_response = norm_opt
            draft.self_raw_input = f"[Correction]: {new_value}"
        elif target == "partner_expectation":
            draft.partner_expectation = norm_opt
            draft.partner_raw_input = f"[Correction]: {new_value}"
        else:
            raise ValueError(f"Invalid correction target '{target}'. Must be 'self_behavior' or 'partner_expectation'.")

        self._update_progress(working)
        self.state_manager.save_session(working)
        return self._build_turn_result(working)

    def get_assessment_state(self, assessment_id: str) -> AssessmentState:
        state = self.state_manager.get_session(assessment_id)
        if not state:
            raise ValueError(f"Unknown assessment ID '{assessment_id}'.")
        return state

    def get_completed_responses(self, assessment_id: str) -> List[ScenarioResponse]:
        """
        Converts collected scenario draft responses into canonical ScenarioResponse objects.
        Validates completeness before conversion.
        """
        state = self.get_assessment_state(assessment_id)
        responses: List[ScenarioResponse] = []

        for sid in state.selected_scenario_ids:
            draft = state.collected_responses.get(sid)
            if not draft or not draft.is_complete():
                raise ValueError(f"Cannot generate ScenarioResponse for incomplete scenario '{sid}'.")

            defn = ScenarioCatalog.get_definition(sid)
            if not defn:
                raise ValueError(f"Unknown scenario ID '{sid}'.")

            # Canonical ScenarioResponse representation for MatchLens reciprocal engine:
            # - perspective="self_behavior"
            # - normalized_preference=user's self behavior
            # - expected_partner_preference=user's expected partner behavior
            # - raw_answer=composite raw string
            # - importance=validated importance weight
            composite_raw = f"Self: {draft.self_raw_input or draft.self_response} | Partner: {draft.partner_raw_input or draft.partner_expectation}"
            scen_resp = ScenarioResponse(
                scenario_id=sid,
                target_dimension=defn.target_dimension,
                perspective="self_behavior",
                normalized_preference=draft.self_response,
                expected_partner_preference=draft.partner_expectation,
                raw_answer=composite_raw,
                importance=draft.importance,
            )
            responses.append(scen_resp)

        return responses

    def confirm_assessment(self, assessment_id: str) -> AssessmentTurnResult:
        """
        Explicitly confirms and completes the assessment.
        Requires assessment status to be READY_FOR_REVIEW and all scenarios to have complete responses.
        """
        state = self.state_manager.get_session(assessment_id)
        if not state:
            raise ValueError(f"Unknown assessment ID '{assessment_id}'.")

        # Fix P2: Require status to be READY_FOR_REVIEW
        if state.status == AssessmentStatus.COMPLETED:
            raise ValueError(f"Assessment '{assessment_id}' is already completed and confirmed.")

        if state.status != AssessmentStatus.READY_FOR_REVIEW:
            raise ValueError(
                f"Cannot confirm assessment in status '{state.status.value}'. "
                "Assessment must be in 'ready_for_review' state before confirming."
            )

        # Verify all scenarios are complete
        incomplete = [
            sid for sid in state.selected_scenario_ids
            if not state.collected_responses.get(sid) or not state.collected_responses[sid].is_complete()
        ]
        if incomplete:
            raise ValueError(f"Cannot confirm incomplete assessment. Missing responses for: {incomplete}.")

        if state.unresolved_clarification:
            raise ValueError("Cannot confirm assessment with unresolved clarification request.")

        working = deepcopy(state)
        working.status = AssessmentStatus.COMPLETED
        working.current_stage = AssessmentStage.COMPLETED
        working.updated_at = datetime.now(timezone.utc)
        self._update_progress(working)
        self.state_manager.save_session(working)

        return self._build_turn_result(working)

    # --- Helper methods ---

    def _advance_to_next_scenario_or_review(self, state: AssessmentState) -> None:
        state.current_scenario_index += 1
        if state.current_scenario_index >= len(state.selected_scenario_ids):
            state.status = AssessmentStatus.READY_FOR_REVIEW
            state.current_stage = AssessmentStage.REVIEW
        else:
            state.current_stage = AssessmentStage.SELF_BEHAVIOR

    def _update_progress(self, state: AssessmentState) -> None:
        total = len(state.selected_scenario_ids)
        completed = [
            sid for sid in state.selected_scenario_ids
            if state.collected_responses.get(sid) and state.collected_responses[sid].is_complete()
        ]

        if state.status == AssessmentStatus.COMPLETED:
            pct = 100.0
        elif state.status == AssessmentStatus.READY_FOR_REVIEW:
            pct = 100.0
        else:
            # Each scenario has 2 parts (self + partner)
            num_parts_total = total * 2
            parts_done = 0
            for sid in state.selected_scenario_ids:
                d = state.collected_responses.get(sid)
                if d:
                    if d.self_response: parts_done += 1
                    if d.partner_expectation: parts_done += 1
            pct = round((parts_done / num_parts_total) * 100.0, 1) if num_parts_total > 0 else 0.0

        state.progress = AssessmentProgress(
            current_scenario_index=state.current_scenario_index,
            total_scenarios=total,
            completed_scenario_ids=completed,
            current_stage=state.current_stage,
            percentage=pct,
        )

    def _build_turn_result(
        self,
        state: AssessmentState,
        override_prompt: Optional[str] = None,
    ) -> AssessmentTurnResult:
        if state.unresolved_clarification:
            prompt_text = (
                f"[Clarification Required]: {state.unresolved_clarification.clarification_prompt}"
            )
            curr_sid = state.unresolved_clarification.scenario_id
            defn = ScenarioCatalog.get_definition(curr_sid)
            return AssessmentTurnResult(
                assessment_id=state.assessment_id,
                status=state.status,
                current_stage=state.current_stage,
                current_scenario_id=curr_sid,
                scenario_definition=defn,
                prompt_text=prompt_text,
                allowed_options=defn.allowed_options if defn else [],
                unresolved_clarification=state.unresolved_clarification,
                progress=state.progress,
            )

        if override_prompt:
            prompt_text = override_prompt
            curr_sid = (
                state.selected_scenario_ids[state.current_scenario_index]
                if state.current_scenario_index < len(state.selected_scenario_ids)
                else None
            )
            defn = ScenarioCatalog.get_definition(curr_sid) if curr_sid else None
            return AssessmentTurnResult(
                assessment_id=state.assessment_id,
                status=state.status,
                current_stage=state.current_stage,
                current_scenario_id=curr_sid,
                scenario_definition=defn,
                prompt_text=prompt_text,
                allowed_options=defn.allowed_options if defn else [],
                progress=state.progress,
            )

        if state.status == AssessmentStatus.COMPLETED:
            return AssessmentTurnResult(
                assessment_id=state.assessment_id,
                status=state.status,
                current_stage=AssessmentStage.COMPLETED,
                prompt_text="Scenario assessment is complete! Responses are confirmed and ready for matching.",
                progress=state.progress,
            )

        if state.status == AssessmentStatus.READY_FOR_REVIEW:
            summary_dict = {
                sid: {
                    "self_response": state.collected_responses[sid].self_response,
                    "partner_expectation": state.collected_responses[sid].partner_expectation,
                }
                for sid in state.selected_scenario_ids
            }
            return AssessmentTurnResult(
                assessment_id=state.assessment_id,
                status=state.status,
                current_stage=AssessmentStage.REVIEW,
                prompt_text="All scenarios answered! Please review your self-responses and partner expectations below. Type 'confirm' to finalize.",
                summary_data=summary_dict,
                progress=state.progress,
            )

        # Active state: generate prompt for current scenario and stage
        curr_sid = state.selected_scenario_ids[state.current_scenario_index]
        defn = ScenarioCatalog.get_definition(curr_sid)
        if not defn:
            raise ValueError(f"Unknown scenario ID '{curr_sid}'.")

        opts_formatted = "\n".join(
            [f"  - {opt}: {defn.option_descriptions.get(opt, '') if defn.option_descriptions else ''}" for opt in defn.allowed_options]
        )

        if state.current_stage == AssessmentStage.SELF_BEHAVIOR:
            prompt_text = (
                f"--- Scenario {state.current_scenario_index + 1}/{len(state.selected_scenario_ids)}: {defn.title} ---\n"
                f"{defn.description or ''}\n\n"
                f"Part A (Your Behavior):\n{defn.self_prompt or 'What would you most likely do in this situation?'}\n\n"
                f"Options:\n{opts_formatted}"
            )
        else:
            prompt_text = (
                f"--- Scenario {state.current_scenario_index + 1}/{len(state.selected_scenario_ids)}: {defn.title} ---\n"
                f"Part B (Partner Expectation):\n{defn.partner_prompt or 'What would you prefer or be comfortable with your partner doing?'}\n\n"
                f"Options:\n{opts_formatted}"
            )

        return AssessmentTurnResult(
            assessment_id=state.assessment_id,
            status=state.status,
            current_stage=state.current_stage,
            current_scenario_id=curr_sid,
            scenario_definition=defn,
            prompt_text=prompt_text,
            allowed_options=defn.allowed_options,
            progress=state.progress,
        )
