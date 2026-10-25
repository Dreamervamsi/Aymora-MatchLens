"""
In-memory profile repository for Phase 6.
"""

import logging
from copy import deepcopy
from typing import Dict, List, Optional
from matchlens.models.profile import UserProfile

logger = logging.getLogger(__name__)


class ProfileRepository:
    """
    In-memory storage for confirmed UserProfile objects.
    Ensures defensive copies on read/write to prevent accidental mutation.
    """

    def __init__(self) -> None:
        self._profiles: Dict[str, UserProfile] = {}

    def save_profile(self, profile: UserProfile, overwrite: bool = False) -> UserProfile:
        """
        Validates and saves a confirmed UserProfile.
        Prevents accidental overwrite unless overwrite=True.
        """
        # Schema validation check
        validated = UserProfile.model_validate(profile.model_dump())

        if validated.user_id in self._profiles and not overwrite:
            raise ValueError(
                f"Profile for user_id '{validated.user_id}' already exists. Use overwrite=True to update."
            )

        self._profiles[validated.user_id] = deepcopy(validated)
        logger.info(f"Saved profile for user '{validated.user_id}' in repository.")
        return deepcopy(self._profiles[validated.user_id])

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Retrieves a profile by user_id. Returns a defensive copy if found.
        """
        profile = self._profiles.get(user_id)
        if not profile:
            return None
        return deepcopy(profile)

    def update_profile(self, profile: UserProfile) -> UserProfile:
        """
        Updates an existing profile. Raises ValueError if profile does not exist.
        """
        if profile.user_id not in self._profiles:
            raise ValueError(f"Profile for user_id '{profile.user_id}' does not exist in repository.")
        return self.save_profile(profile, overwrite=True)

    def list_profiles(self) -> List[UserProfile]:
        """
        Returns defensive copies of all saved user profiles.
        """
        return [deepcopy(p) for p in self._profiles.values()]

    def clear(self) -> None:
        """
        Clears all stored profiles (useful for test resets).
        """
        self._profiles.clear()
