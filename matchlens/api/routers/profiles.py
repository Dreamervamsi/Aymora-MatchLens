"""
Profile management endpoints router.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from matchlens.api.dependencies import get_profile_repository
from matchlens.api.repository import ProfileRepository
from matchlens.models.profile import UserProfile

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: str,
    repository: ProfileRepository = Depends(get_profile_repository),
) -> UserProfile:
    """
    Retrieves a confirmed UserProfile by user_id from the repository.
    """
    profile = repository.get_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile for user_id '{user_id}' was not found.",
        )
    return profile
