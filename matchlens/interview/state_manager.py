import logging
import uuid
from typing import Dict, Optional
from matchlens.interview.models import InterviewState
from matchlens.models.profile import UserProfile

logger = logging.getLogger(__name__)


class InterviewStateManager:
    """
    In-memory registry for InterviewState objects.
    Provides session creation, retrieval, updates, and JSON serialization/reconstruction capabilities.
    """

    def __init__(self):
        self._sessions: Dict[str, InterviewState] = {}

    def create_session(self, user_id: str, session_id: Optional[str] = None) -> InterviewState:
        """
        Creates a new interview session state for a user.

        Args:
            user_id: Unique user identifier
            session_id: Optional custom session ID; generates UUID4 if None

        Returns:
            Newly initialized InterviewState
        """
        sid = session_id or f"session_{uuid.uuid4().hex[:12]}"
        initial_profile = UserProfile(user_id=user_id)
        
        state = InterviewState(
            session_id=sid,
            user_id=user_id,
            draft_profile=initial_profile,
        )
        self._sessions[sid] = state
        return state

    def get_session(self, session_id: str) -> Optional[InterviewState]:
        """
        Retrieves interview state by session ID.
        """
        return self._sessions.get(session_id)

    def save_session(self, state: InterviewState) -> None:
        """
        Saves/updates interview state in registry.
        """
        self._sessions[state.session_id] = state

    def delete_session(self, session_id: str) -> bool:
        """
        Deletes a session state from registry.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def serialize_state(self, session_id: str) -> str:
        """
        Serializes interview state to JSON string.
        """
        state = self.get_session(session_id)
        if not state:
            raise ValueError(f"Session ID '{session_id}' not found.")
        return state.model_dump_json()

    def deserialize_state(self, json_data: str) -> InterviewState:
        """
        Reconstructs InterviewState from JSON string and stores in registry.
        """
        state = InterviewState.model_validate_json(json_data)
        self.save_session(state)
        return state
