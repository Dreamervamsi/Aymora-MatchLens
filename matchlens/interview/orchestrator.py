import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from copy import deepcopy

from matchlens.ai.extractor import GroqProfileExtractor
from matchlens.ai.models import ExtractedProfileUpdate, PartialUserAttributes, PartialPartnerPreferences, PartialDealbreakers
from matchlens.interview.config import InterviewSettings
from matchlens.interview.models import (
    ChatMessage,
    InterviewProgress,
    InterviewState,
    InterviewStatus,
    InterviewTopic,
    InterviewTurnResult,
    PendingConfirmation,
    TOPIC_ORDER,
)
from matchlens.interview.question_selector import HybridQuestionSelector
from matchlens.interview.state_manager import InterviewStateManager
from matchlens.models.profile import UserProfile, UserAttributes, PartnerPreferences, Dealbreakers

logger = logging.getLogger(__name__)

EARLY_FINISH_TRIGGERS = [
    "finish",
    "stop",
    "done",
    "skip",
    "wrap up",
    "that's all",
    "thats all",
    "end interview",
]

AFFIRMATIVE_PATTERNS = [
    r"\byes\b", r"\byeah\b", r"\byep\b", r"\bsure\b", r"\bcorrect\b",
    r"\babsolutely\b", r"\bthat's right\b", r"\bthats right\b", r"\bi do\b", r"\btrue\b"
]
NEGATIVE_PATTERNS = [
    r"\bno\b", r"\bnope\b", r"\bnah\b", r"\bincorrect\b", r"\bfalse\b",
    r"\bwrong\b", r"\bi don't\b", r"\bi dont\b", r"\bnot really\b"
]
QUALIFIED_AMBIGUOUS_PATTERNS = [
    r"\bmaybe\b", r"\bsometimes\b", r"\bdepends\b", r"\bpartially\b",
    r"\bnot sure\b", r"\bi guess\b", r"\bkind of\b", r"\bsort of\b"
]


def is_early_finish_request(text: str) -> bool:
    cleaned = text.strip().lower()
    words = cleaned.split()
    if len(words) > 10:
        return False
    return any(trig in cleaned for trig in EARLY_FINISH_TRIGGERS)


class InterviewOrchestrator:
    """
    Main orchestration engine for stateful, adaptive conversational onboarding interviews in MatchLens.
    Refactored with atomic turn processing and strict validation rules.
    """

    def __init__(
        self,
        settings: Optional[InterviewSettings] = None,
        state_manager: Optional[InterviewStateManager] = None,
        extractor: Optional[GroqProfileExtractor] = None,
        question_selector: Optional[HybridQuestionSelector] = None,
    ):
        self.settings = settings or InterviewSettings()
        self.state_manager = state_manager or InterviewStateManager()
        self.extractor = extractor or GroqProfileExtractor()
        self.question_selector = question_selector or HybridQuestionSelector()

    def start_interview(self, user_id: str, session_id: Optional[str] = None) -> tuple[InterviewState, str]:
        """
        Initializes a new interview session and generates the opening question.
        """
        state = self.state_manager.create_session(user_id=user_id, session_id=session_id)
        opening_q_id = "basic_and_intention.default"
        opening_msg = (
            "Welcome to MatchLens! I'm here to help you build a scenario-aware matchmaking profile through a brief conversation. "
            "To get started, could you tell me a bit about yourself—such as your age, gender, and what kind of relationship you're looking for?"
        )
        
        state.conversation_history.append(ChatMessage(role="assistant", content=opening_msg))
        state.previously_asked_question_ids.append(opening_q_id)
        state.progress = self._calculate_progress(state)
        self.state_manager.save_session(state)
        
        return state, opening_msg

    async def process_turn(self, session_id: str, user_message: str) -> InterviewTurnResult:
        """
        Processes a single conversational turn atomically.
        If an operation or AI call fails, state remains unmutated.
        """
        state = self.state_manager.get_session(session_id)
        if not state:
            raise ValueError(f"Session ID '{session_id}' was not found.")

        cleaned_input = (user_message or "").strip()
        if not cleaned_input:
            assistant_msg = "I didn't catch that. Could you please provide a response?"
            return self._build_turn_result(state, assistant_msg, newly_extracted=[])

        if state.status == InterviewStatus.COMPLETED:
            return self._build_turn_result(
                state,
                "Your profile interview is already completed and confirmed! You can review your profile anytime.",
                newly_extracted=[],
            )

        # Work on a deep copy for atomic turn execution
        working_state = deepcopy(state)
        working_state.turn_count += 1
        working_state.conversation_history.append(ChatMessage(role="user", content=cleaned_input))

        # Check early finish intent
        if self.settings.allow_early_finish and is_early_finish_request(cleaned_input):
            working_state.status = InterviewStatus.READY_FOR_REVIEW
            working_state.pending_confirmations.clear()  # Discard unconfirmed proposals on finish
            working_state.progress = self._calculate_progress(working_state)
            closing_msg = "Got it! We can stop here. Your draft profile is ready for your review."
            working_state.conversation_history.append(ChatMessage(role="assistant", content=closing_msg))
            self.state_manager.save_session(working_state)
            return self._build_turn_result(working_state, closing_msg, newly_extracted=[], is_ready=True)

        newly_extracted: List[str] = []
        is_confirmation_turn = False

        # 1. Handle pending confirmation if active
        if working_state.pending_confirmations:
            resolved, result_code, msg = self._process_pending_confirmation(working_state, cleaned_input)
            if result_code in ("confirmed", "rejected"):
                is_confirmation_turn = True
                if resolved:
                    newly_extracted.extend(resolved)
            elif result_code == "ambiguous":
                # User gave ambiguous/qualified response to confirmation prompt
                # Do NOT change profile, ask for explicit confirmation again
                reask_msg = f"I want to make sure I understand correctly. {working_state.pending_confirmations[0].clarification_question}"
                working_state.conversation_history.append(ChatMessage(role="assistant", content=reask_msg))
                self.state_manager.save_session(working_state)
                return self._build_turn_result(working_state, reask_msg, newly_extracted=[])

        # 2. General AI extraction (SKIP if this turn was exclusively resolving a confirmation)
        if not is_confirmation_turn:
            context_prompt = f"Current interview topic: '{working_state.current_topic.value}'."
            try:
                extracted_update = await self.extractor.extract_from_text(
                    user_input=cleaned_input,
                    context_prompt=context_prompt,
                )
                extracted_fields = self._merge_extracted_data(working_state, extracted_update)
                newly_extracted.extend(extracted_fields)
            except Exception as e:
                logger.error(f"Groq profile extraction failed on turn {working_state.turn_count}: {e}")
                # Atomic rollback: do not save working_state
                fallback_msg = "I had a moment of trouble processing that. Could you rephrase or repeat your response?"
                state.conversation_history.append(ChatMessage(role="assistant", content=fallback_msg))
                self.state_manager.save_session(state)
                return self._build_turn_result(state, fallback_msg, newly_extracted=[])

        # 3. Topic turn tracking & progression
        current_topic_str = working_state.current_topic.value
        working_state.topic_turn_counts[current_topic_str] = working_state.topic_turn_counts.get(current_topic_str, 0) + 1

        if self._should_advance_topic(working_state):
            working_state.current_topic = self._get_next_topic(working_state.current_topic)

        # 4. Overall readiness & max turn check
        missing_essential = self._get_missing_essential_fields(working_state)
        max_turns_reached = working_state.turn_count >= self.settings.max_total_turns
        all_topics_covered = (working_state.current_topic == InterviewTopic.DEALBREAKERS and len(self._get_missing_fields_for_topic(working_state, InterviewTopic.DEALBREAKERS)) == 0)

        if max_turns_reached or (len(missing_essential) == 0 and all_topics_covered):
            working_state.status = InterviewStatus.READY_FOR_REVIEW
            working_state.pending_confirmations.clear()  # Clear pending proposals when review ready

        # 5. Question selection (selecting field from ACTIVE topic, preventing repeat questions)
        if working_state.pending_confirmations:
            working_state.status = InterviewStatus.AWAITING_CONFIRMATION
            next_conf = working_state.pending_confirmations[0]
            q_id = f"confirm.{next_conf.field_name}"
            assistant_question = next_conf.clarification_question
        elif working_state.status == InterviewStatus.READY_FOR_REVIEW:
            q_id = "review_prompt"
            assistant_question = (
                "Thank you! We've gathered enough information for your profile. "
                "Your draft profile is now ready for your review!"
            )
        else:
            working_state.status = InterviewStatus.ACTIVE
            target_topic_missing = self._get_missing_fields_for_topic(working_state, working_state.current_topic)
            target_field = target_topic_missing[0] if target_topic_missing else None
            
            q_id, assistant_question = await self._select_non_repeating_question(
                state=working_state,
                target_topic=working_state.current_topic,
                missing_field_key=target_field,
            )

        working_state.conversation_history.append(ChatMessage(role="assistant", content=assistant_question))
        if q_id not in working_state.previously_asked_question_ids:
            working_state.previously_asked_question_ids.append(q_id)

        # Calculate progress & commit state
        working_state.progress = self._calculate_progress(working_state)
        self.state_manager.save_session(working_state)

        return self._build_turn_result(
            state=working_state,
            assistant_message=assistant_question,
            newly_extracted=list(set(newly_extracted)),
            is_ready=(working_state.status == InterviewStatus.READY_FOR_REVIEW),
        )

    def confirm_draft_profile(self, session_id: str) -> UserProfile:
        state = self.state_manager.get_session(session_id)
        if not state:
            raise ValueError(f"Session ID '{session_id}' not found.")
            
        if state.status != InterviewStatus.READY_FOR_REVIEW and not state.progress.essential_fields_satisfied:
            raise ValueError(
                f"Cannot confirm profile in status '{state.status.value}'. "
                "Interview must be in 'ready_for_review' state or have all essential fields satisfied before finalizing."
            )

        if state.pending_confirmations:
            raise ValueError("Cannot finalize profile while unconfirmed inferences exist in pending confirmations.")

        state.status = InterviewStatus.COMPLETED
        state.progress.percentage = 100.0
        self.state_manager.save_session(state)
        return state.draft_profile

    def get_draft_profile(self, session_id: str) -> UserProfile:
        state = self.state_manager.get_session(session_id)
        if not state:
            raise ValueError(f"Session ID '{session_id}' not found.")
        return state.draft_profile

    # --- Internal Helpers ---

    def _process_pending_confirmation(self, state: InterviewState, user_input: str) -> tuple[List[str], str, str]:
        """
        Parses explicit affirmative or negative responses to pending confirmations.
        Returns tuple of (resolved_fields, status_code, message).
        status_code is 'confirmed', 'rejected', or 'ambiguous'.
        """
        if not state.pending_confirmations:
            return [], "none", ""

        pending = state.pending_confirmations[0]
        cleaned = user_input.strip().lower()

        # Any qualifying or hesitant phrase makes confirmation ambiguous
        if any(re.search(pat, cleaned) for pat in QUALIFIED_AMBIGUOUS_PATTERNS):
            return [], "ambiguous", f"Qualified/hesitant response '{user_input}' for {pending.field_name}"

        is_affirmative = any(re.search(pat, cleaned) for pat in AFFIRMATIVE_PATTERNS)
        is_negative = any(re.search(pat, cleaned) for pat in NEGATIVE_PATTERNS)

        # If both affirmative and negative cues are found, treat as ambiguous/contradictory
        if is_affirmative and is_negative:
            return [], "ambiguous", f"Contradictory response '{user_input}' for {pending.field_name}"

        if is_affirmative and not is_negative:
            cat = pending.target_category
            field = pending.field_name
            val = pending.proposed_value

            if self._safely_update_profile(state.draft_profile, cat, field, val):
                state.pending_confirmations.pop(0)
                return [f"{cat}.{field}"], "confirmed", f"Confirmed {field} = {val}"
            else:
                state.pending_confirmations.pop(0)
                return [], "rejected", f"Validation failed for proposed value {val} on {field}"

        elif is_negative and not is_affirmative:
            state.pending_confirmations.pop(0)
            return [], "rejected", f"Rejected proposed value for {pending.field_name}"

        return [], "ambiguous", f"Response '{user_input}' was ambiguous for confirmation"

    def _merge_extracted_data(self, state: InterviewState, update: ExtractedProfileUpdate) -> List[str]:
        newly_extracted = []
        p = state.draft_profile

        for field, val in update.confirmed_self_attributes.model_dump(exclude_unset=True).items():
            if val is not None:
                if self._safely_update_profile(p, "self_attributes", field, val):
                    newly_extracted.append(f"attributes.{field}")

        for field, val in update.confirmed_partner_preferences.model_dump(exclude_unset=True).items():
            if val is not None:
                if self._safely_update_profile(p, "partner_preferences", field, val):
                    newly_extracted.append(f"expectations.{field}")

        for field, val in update.confirmed_dealbreakers.model_dump(exclude_unset=True).items():
            if val is not None:
                if self._safely_update_profile(p, "dealbreakers", field, val):
                    newly_extracted.append(f"dealbreakers.{field}")

        for sc in update.scenarios:
            if not any(s.scenario_id == sc.scenario_id for s in p.scenarios):
                p.scenarios.append(sc)
                newly_extracted.append(f"scenarios.{sc.scenario_id}")

        for conf_prompt in update.confirmations_needed:
            pending = PendingConfirmation.from_confirmation_prompt(conf_prompt)
            if not any(pc.field_name == pending.field_name and pc.target_category == pending.target_category for pc in state.pending_confirmations):
                state.pending_confirmations.append(pending)

        return newly_extracted

    def _safely_update_profile(self, profile: UserProfile, category: str, field: str, value: Any) -> bool:
        """
        Validates attribute update against Pydantic schema before mutating profile.
        Returns True if update succeeded, False if validation failed.
        """
        try:
            if category == "self_attributes":
                current_dict = profile.attributes.model_dump()
                current_dict[field] = value
                validated = UserAttributes.model_validate(current_dict)
                profile.attributes = validated
                return True
            elif category == "partner_preferences":
                current_dict = profile.expectations.model_dump()
                current_dict[field] = value
                validated = PartnerPreferences.model_validate(current_dict)
                profile.expectations = validated
                return True
            elif category == "dealbreakers":
                current_dict = profile.dealbreakers.model_dump()
                current_dict[field] = value
                validated = Dealbreakers.model_validate(current_dict)
                profile.dealbreakers = validated
                return True
        except Exception as e:
            logger.warning(f"Profile update validation failed for {category}.{field} = {value}: {e}")
            return False
        return False

    async def _select_non_repeating_question(
        self,
        state: InterviewState,
        target_topic: InterviewTopic,
        missing_field_key: Optional[str],
    ) -> tuple[str, str]:
        """
        Selects question ensuring question_id has not already been asked in this session.
        """
        q_id, q_text = await self.question_selector.select_and_generate_question(
            state=state,
            target_topic=target_topic,
            missing_field_key=missing_field_key,
        )

        if q_id not in state.previously_asked_question_ids:
            return q_id, q_text

        # Fallback: search for an unasked question in current or subsequent topics
        topic_missing = self._get_missing_fields_for_topic(state, target_topic)
        for alternative_field in topic_missing:
            alt_id = f"{target_topic.value}.{alternative_field}"
            if alt_id not in state.previously_asked_question_ids:
                return await self.question_selector.select_and_generate_question(
                    state=state,
                    target_topic=target_topic,
                    missing_field_key=alternative_field,
                )

        # Ultimate unique fallback ID if all topic default questions were asked
        fallback_unique_id = f"{target_topic.value}.q_{len(state.previously_asked_question_ids) + 1}"
        return fallback_unique_id, q_text

    def _should_advance_topic(self, state: InterviewState) -> bool:
        topic_str = state.current_topic.value
        turns_in_topic = state.topic_turn_counts.get(topic_str, 0)
        
        if turns_in_topic >= self.settings.max_turns_per_topic:
            return True

        missing_topic_fields = self._get_missing_fields_for_topic(state, state.current_topic)
        return len(missing_topic_fields) == 0

    def _get_next_topic(self, current: InterviewTopic) -> InterviewTopic:
        try:
            idx = TOPIC_ORDER.index(current)
            if idx + 1 < len(TOPIC_ORDER):
                return TOPIC_ORDER[idx + 1]
        except ValueError:
            pass
        return InterviewTopic.DEALBREAKERS

    def _get_missing_essential_fields(self, state: InterviewState) -> List[str]:
        missing = []
        p = state.draft_profile

        for f in self.settings.essential_self_fields:
            if getattr(p.attributes, f, None) is None:
                missing.append(f"attributes.{f}")

        for f in self.settings.essential_partner_fields:
            val = getattr(p.expectations, f, None)
            if val is None or (isinstance(val, list) and len(val) == 0):
                missing.append(f"expectations.{f}")

        return missing

    def _get_missing_fields_for_topic(self, state: InterviewState, topic: InterviewTopic) -> List[str]:
        p = state.draft_profile
        missing = []

        if topic == InterviewTopic.BASIC_AND_INTENTION:
            if p.attributes.age is None: missing.append("age")
            if p.attributes.gender is None: missing.append("gender")
            if p.attributes.relationship_intent is None: missing.append("relationship_intent")
        elif topic == InterviewTopic.CORE_VALUES:
            if p.attributes.core_values is None: missing.append("core_values")
        elif topic == InterviewTopic.LIFESTYLE:
            if p.attributes.smoking is None: missing.append("smoking")
            if p.attributes.drinking is None: missing.append("drinking")
            if p.attributes.wants_children is None: missing.append("wants_children")
        elif topic == InterviewTopic.COMMUNICATION:
            if p.attributes.communication_style is None: missing.append("communication_style")
            if p.attributes.conflict_resolution is None: missing.append("conflict_resolution")
        elif topic == InterviewTopic.PARTNER_EXPECTATIONS:
            if not p.expectations.acceptable_genders: missing.append("acceptable_genders")
            if p.expectations.desired_intentions is None: missing.append("desired_intentions")
        elif topic == InterviewTopic.DEALBREAKERS:
            pass

        return missing

    def _calculate_progress(self, state: InterviewState) -> InterviewProgress:
        current_idx = TOPIC_ORDER.index(state.current_topic) if state.current_topic in TOPIC_ORDER else 0
        completed_topics = TOPIC_ORDER[:current_idx]
        
        pct = (current_idx / len(TOPIC_ORDER)) * 100.0
        missing_essential = self._get_missing_essential_fields(state)
        essential_satisfied = len(missing_essential) == 0

        if state.status in (InterviewStatus.READY_FOR_REVIEW, InterviewStatus.COMPLETED):
            pct = 100.0

        return InterviewProgress(
            completed_topics=completed_topics,
            current_topic=state.current_topic,
            percentage=round(pct, 1),
            essential_fields_satisfied=essential_satisfied,
        )

    def _build_turn_result(
        self,
        state: InterviewState,
        assistant_message: str,
        newly_extracted: List[str],
        is_ready: bool = False,
    ) -> InterviewTurnResult:
        missing_essential = self._get_missing_essential_fields(state)
        return InterviewTurnResult(
            session_id=state.session_id,
            assistant_message=assistant_message,
            interview_status=state.status,
            current_topic=state.current_topic,
            progress=state.progress,
            newly_extracted_fields=newly_extracted,
            pending_confirmations=state.pending_confirmations,
            missing_essential_fields=missing_essential,
            is_ready_for_review=is_ready or (state.status == InterviewStatus.READY_FOR_REVIEW),
        )
