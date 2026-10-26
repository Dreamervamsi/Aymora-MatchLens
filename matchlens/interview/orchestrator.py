import logging
import re
from typing import Any, AsyncGenerator, Dict, List, Optional, Set, Tuple
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

EXPLICIT_EARLY_FINISH_COMMANDS = {
    "/finish", "/stop", "/done", "/skip",
    "finish", "stop", "done", "skip", "wrap up",
    "skip rest", "that's all", "thats all", "end interview"
}

EARLY_FINISH_PATTERNS = [
    r"^\s*/?(finish|stop|done|skip)\s*$",
    r"^\s*(please\s+)?(i\s+(want|would\s+like)\s+to\s+)?(finish|stop|end|wrap\s*up)(\s+(the|this)?\s*interview)?(\s+(now|here|please))?\s*$",
    r"^\s*(i'm|im|i\s+am)\s+done(\s+now|\s+here|\s+with\s+this)?\s*$",
    r"^\s*(skip\s+rest|that's\s+all|thats\s+all)\s*$",
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
    if cleaned in EXPLICIT_EARLY_FINISH_COMMANDS:
        return True
    
    # Check bounded regex patterns
    for pat in EARLY_FINISH_PATTERNS:
        if re.search(pat, cleaned):
            return True
            
    return False


class InterviewOrchestrator:
    """
    Main orchestration engine for stateful, adaptive conversational onboarding interviews in MatchLens.
    Refactored with atomic turn processing, non-repeating question enforcement, and strict draft profile validation.
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
            working_state.status = InterviewStatus.PROCESSING_EXTRACTION
            working_state.pending_confirmations.clear()  # Discard unconfirmed proposals on finish
            working_state.progress = self._calculate_progress(working_state)
            closing_msg = "Got it! We can stop here. We are now organizing your responses into your profile."
            working_state.conversation_history.append(ChatMessage(role="assistant", content=closing_msg))
            self.state_manager.save_session(working_state)

            # Trigger single batch extraction
            try:
                extracted_update = await self.extractor.extract_full_profile_batch(working_state.conversation_history)
                self._merge_extracted_data(working_state, extracted_update)
                working_state.status = InterviewStatus.READY_FOR_REVIEW
                review_msg = "Your draft profile is now ready for your review!"
                working_state.conversation_history.append(ChatMessage(role="assistant", content=review_msg))
                self.state_manager.save_session(working_state)
                return self._build_turn_result(working_state, review_msg, newly_extracted=[], is_ready=True)
            except Exception as e:
                logger.error(f"Batch profile extraction failed on early finish: {e}")
                working_state.status = InterviewStatus.READY_FOR_REVIEW
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
                if result_code == "rejected":
                    # Check for simple affirmative/negative rejections vs text with explicit correction details
                    simple_rejections = {"no", "nope", "nah", "incorrect", "false", "wrong"}
                    if cleaned_input.lower().strip(" .!?,") in simple_rejections:
                        logger.info("Simple rejection detected without explicit correction; skipping extra LLM extraction.")
                    else:
                        # Extract explicit corrections provided in the rejection message (e.g. "No, I smoke socially")
                        try:
                            corr_update = await self.extractor.extract_from_text(
                                user_input=cleaned_input,
                                context_prompt=f"User rejected proposed value for '{msg}'. Extract any explicit correction or new value.",
                            )
                            corr_fields = self._merge_extracted_data(working_state, corr_update, ignore_confirmations=True)
                            newly_extracted.extend(corr_fields)
                        except Exception as e:
                            logger.warning(f"Failed to extract explicit correction during rejection: {e}")
            elif result_code == "ambiguous":
                reask_msg = f"I want to make sure I understand correctly. {working_state.pending_confirmations[0].clarification_question}"
                working_state.conversation_history.append(ChatMessage(role="assistant", content=reask_msg))
                self.state_manager.save_session(working_state)
                return self._build_turn_result(working_state, reask_msg, newly_extracted=[])

        # 2. Extract profile updates during turn
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
        dealbreaker_qs = {"dealbreakers.default", "dealbreakers.dealbreakers"}
        dealbreakers_asked = any(q in working_state.previously_asked_question_ids for q in dealbreaker_qs)
        all_topics_covered = (working_state.current_topic == InterviewTopic.DEALBREAKERS and dealbreakers_asked)

        if max_turns_reached or all_topics_covered or (len(missing_essential) == 0 and working_state.current_topic == InterviewTopic.DEALBREAKERS):
            working_state.status = InterviewStatus.PROCESSING_EXTRACTION
            working_state.pending_confirmations.clear()  # Clear pending proposals when review ready
            try:
                extracted_update = await self.extractor.extract_full_profile_batch(working_state.conversation_history)
                self._merge_extracted_data(working_state, extracted_update)
            except Exception as e:
                logger.error(f"Batch profile extraction failed upon completion: {e}")
            working_state.status = InterviewStatus.READY_FOR_REVIEW

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
            
            try:
                q_id, assistant_question = await self._select_non_repeating_question(
                    state=working_state,
                    target_topic=working_state.current_topic,
                    missing_field_key=target_field,
                )
            except Exception as e:
                logger.error(f"Question generation failed on topic '{working_state.current_topic.value}': {e}")
                q_id = f"fallback.{working_state.current_topic.value}.q_{len(working_state.previously_asked_question_ids) + 1}"
                assistant_question = f"Could you tell me a bit more about your {working_state.current_topic.value.replace('_', ' ')} preferences?"

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

    async def process_turn_stream(
        self, session_id: str, user_message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Processes a conversational turn asynchronously, yielding token content deltas
        and concluding with a final turn metadata event.
        """
        turn_result = await self.process_turn(session_id=session_id, user_message=user_message)
        assistant_message = turn_result.assistant_message

        # Stream assistant_message tokens chunk by chunk
        words = assistant_message.split(" ")
        for i, word in enumerate(words):
            delta = word if i == len(words) - 1 else word + " "
            yield {"type": "content_delta", "delta": delta}

        final_data = {
            "session_id": turn_result.session_id,
            "assistant_message": turn_result.assistant_message,
            "interview_status": turn_result.interview_status.value if hasattr(turn_result.interview_status, 'value') else turn_result.interview_status,
            "current_topic": turn_result.current_topic.value if hasattr(turn_result.current_topic, 'value') else turn_result.current_topic,
            "progress": turn_result.progress.model_dump() if hasattr(turn_result.progress, 'model_dump') else turn_result.progress,
            "newly_extracted_fields": turn_result.newly_extracted_fields,
            "pending_confirmations": [c.model_dump() if hasattr(c, 'model_dump') else c for c in turn_result.pending_confirmations],
            "missing_essential_fields": turn_result.missing_essential_fields,
            "is_ready_for_review": turn_result.is_ready_for_review,
        }
        yield {"type": "turn_complete", "data": final_data}

    async def execute_batch_extraction(self, session_id: str) -> InterviewState:
        """
        Executes or retries single batch AI profile extraction for a given interview session.
        Idempotent: updates draft profile and transitions status to READY_FOR_REVIEW upon success.
        """
        state = self.state_manager.get_session(session_id)
        if not state:
            raise ValueError(f"Session ID '{session_id}' not found.")

        state.status = InterviewStatus.PROCESSING_EXTRACTION
        self.state_manager.save_session(state)

        try:
            extracted_update = await self.extractor.extract_full_profile_batch(state.conversation_history)
            self._merge_extracted_data(state, extracted_update)
            state.status = InterviewStatus.READY_FOR_REVIEW
        except Exception as e:
            logger.error(f"Error during execute_batch_extraction for session {session_id}: {e}")
            state.status = InterviewStatus.READY_FOR_REVIEW

        state.progress = self._calculate_progress(state)
        self.state_manager.save_session(state)
        return state

    def confirm_draft_profile(self, session_id: str, mark_completed: bool = True) -> UserProfile:
        """
        User confirms and finalizes their draft profile.
        Requires status to be READY_FOR_REVIEW and all essential profile fields to be satisfied.
        When mark_completed is False, returns draft profile without updating session status to COMPLETED yet.
        """
        state = self.state_manager.get_session(session_id)
        if not state:
            raise ValueError(f"Session ID '{session_id}' not found.")
            
        if state.status != InterviewStatus.READY_FOR_REVIEW:
            raise ValueError(
                f"Cannot confirm profile in status '{state.status.value}'. "
                "Interview must be in 'ready_for_review' state before finalizing."
            )

        if state.pending_confirmations:
            raise ValueError("Cannot finalize profile while unconfirmed inferences exist in pending confirmations.")

        missing_essential = self._get_missing_essential_fields(state)
        if missing_essential:
            raise ValueError(
                f"Cannot finalize an incomplete profile with missing essential fields: {missing_essential}. "
                "An early-finished or incomplete profile must not produce a match-ready profile until essential information is provided."
            )

        if mark_completed:
            state.status = InterviewStatus.COMPLETED
            state.progress.percentage = 100.0
            self.state_manager.save_session(state)
        return state.draft_profile

    def complete_interview(self, session_id: str) -> None:
        """
        Marks an interview session as completed after profile persistence succeeds.
        """
        state = self.state_manager.get_session(session_id)
        if state:
            state.status = InterviewStatus.COMPLETED
            state.progress.percentage = 100.0
            self.state_manager.save_session(state)

    def get_draft_profile(self, session_id: str) -> UserProfile:
        state = self.state_manager.get_session(session_id)
        if not state:
            raise ValueError(f"Session ID '{session_id}' not found.")
        return state.draft_profile

    # --- Internal Helpers ---

    def _process_pending_confirmation(self, state: InterviewState, user_input: str) -> tuple[List[str], str, str]:
        if not state.pending_confirmations:
            return [], "none", ""

        pending = state.pending_confirmations[0]
        cleaned = user_input.strip().lower()

        if any(re.search(pat, cleaned) for pat in QUALIFIED_AMBIGUOUS_PATTERNS):
            return [], "ambiguous", f"Qualified/hesitant response '{user_input}' for {pending.field_name}"

        is_affirmative = any(re.search(pat, cleaned) for pat in AFFIRMATIVE_PATTERNS)
        is_negative = any(re.search(pat, cleaned) for pat in NEGATIVE_PATTERNS)

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

    def _merge_extracted_data(
        self,
        state: InterviewState,
        update: ExtractedProfileUpdate,
        ignore_confirmations: bool = False,
    ) -> List[str]:
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

        # Note: Scenario extraction is restricted to Phase 5.3 scenario assessment workflow

        if not ignore_confirmations:
            for conf_prompt in update.confirmations_needed:
                pending = PendingConfirmation.from_confirmation_prompt(conf_prompt)
                if not any(pc.field_name == pending.field_name and pc.target_category == pending.target_category for pc in state.pending_confirmations):
                    state.pending_confirmations.append(pending)

        return newly_extracted

    def _safely_update_profile(self, profile: UserProfile, category: str, field: str, value: Any) -> bool:
        try:
            if category == "self_attributes":
                current_dict = profile.attributes.model_dump()
                # Coerce scalar string to list for list-based attributes if needed
                list_fields = {"core_values", "interests"}
                if field in list_fields and isinstance(value, str):
                    value = [v.strip() for v in value.split(",") if v.strip()]
                current_dict[field] = value
                validated = UserAttributes.model_validate(current_dict)
                profile.attributes = validated
                return True
            elif category == "partner_preferences":
                current_dict = profile.expectations.model_dump()
                # Coerce scalar string to list for list-based preference fields
                list_fields = {
                    "acceptable_genders",
                    "desired_intentions",
                    "desired_values",
                    "acceptable_smoking",
                    "acceptable_drinking",
                    "desired_wants_children",
                    "desired_communication_styles",
                    "desired_conflict_resolutions",
                }
                if field in list_fields and isinstance(value, str):
                    value = [v.strip() for v in value.split(",") if v.strip()]
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

    def _is_question_previously_asked(self, state: InterviewState, q_id: str, q_text: str) -> bool:
        """
        Checks if question ID OR question text content has already been asked in this session.
        """
        if q_id in state.previously_asked_question_ids:
            return True

        norm_q = q_text.strip().lower()
        for msg in state.conversation_history:
            if msg.role == "assistant" and msg.content.strip().lower() == norm_q:
                return True

        return False

    async def _select_non_repeating_question(
        self,
        state: InterviewState,
        target_topic: InterviewTopic,
        missing_field_key: Optional[str],
    ) -> tuple[str, str]:
        """
        Selects question ensuring both question_id AND question text content are unique.
        """
        q_id, q_text = await self.question_selector.select_and_generate_question(
            state=state,
            target_topic=target_topic,
            missing_field_key=missing_field_key,
        )

        if not self._is_question_previously_asked(state, q_id, q_text):
            return q_id, q_text

        # Search for an unasked question in missing fields for current or subsequent topics
        topic_missing = self._get_missing_fields_for_topic(state, target_topic)
        for alternative_field in topic_missing:
            alt_id, alt_text = await self.question_selector.select_and_generate_question(
                state=state,
                target_topic=target_topic,
                missing_field_key=alternative_field,
            )
            if not self._is_question_previously_asked(state, alt_id, alt_text):
                return alt_id, alt_text

        # Fallback to unique prompt for topic
        fallback_unique_id = f"{target_topic.value}.q_{len(state.previously_asked_question_ids) + 1}"
        fallback_text = f"Could you share a bit more detail regarding your {target_topic.value.replace('_', ' ')}?"
        return fallback_unique_id, fallback_text

    def _should_advance_topic(self, state: InterviewState) -> bool:
        topic_str = state.current_topic.value
        turns_in_topic = state.topic_turn_counts.get(topic_str, 0)
        
        if turns_in_topic >= self.settings.max_turns_per_topic:
            return True

        from matchlens.interview.question_bank import STRUCTURED_QUESTION_BANK
        topic_q_ids = [q_id for q_id, defn in STRUCTURED_QUESTION_BANK.items() if defn.topic == state.current_topic]
        if topic_q_ids and all(q_id in state.previously_asked_question_ids for q_id in topic_q_ids):
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
        
        missing_essential = self._get_missing_essential_fields(state)
        essential_satisfied = len(missing_essential) == 0

        if state.status == InterviewStatus.COMPLETED:
            pct = 100.0
        elif state.status == InterviewStatus.READY_FOR_REVIEW:
            if essential_satisfied and current_idx >= len(TOPIC_ORDER) - 1:
                pct = 100.0
            else:
                pct = (current_idx / len(TOPIC_ORDER)) * 100.0
        else:
            pct = (current_idx / len(TOPIC_ORDER)) * 100.0

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
