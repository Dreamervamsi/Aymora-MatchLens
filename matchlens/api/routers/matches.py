"""
Reciprocal matching endpoints router.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from matchlens.api.dependencies import get_profile_repository
from matchlens.api.repository import ProfileRepository
from matchlens.api.schemas import MatchRecommendationResponse
from matchlens.engine.ranker import rank_candidates
from matchlens.synthetic.profiles import create_synthetic_profiles

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matches", tags=["Matching"])


@router.get("/{user_id}", response_model=MatchRecommendationResponse)
async def get_top_matches(
    user_id: str,
    top_k: int = Query(default=3, ge=1, le=20),
    repository: ProfileRepository = Depends(get_profile_repository),
) -> MatchRecommendationResponse:
    """
    Returns top reciprocal matches for a confirmed user profile against candidate pool.
    """
    requesting_profile = repository.get_profile(user_id)
    if not requesting_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Confirmed profile for user '{user_id}' was not found. Please confirm interview profile first.",
        )

    # Build candidate pool from synthetic profiles + other confirmed profiles in repository
    synthetic_pool = list(create_synthetic_profiles().values())
    repo_pool = repository.list_profiles()

    candidate_map = {}
    for cand in synthetic_pool + repo_pool:
        if cand.user_id != user_id and cand.user_id not in candidate_map:
            candidate_map[cand.user_id] = cand

    candidates = list(candidate_map.values())

    try:
        top_matches, metadata = rank_candidates(
            requesting_user=requesting_profile,
            candidates=candidates,
            top_k=top_k,
        )

        return MatchRecommendationResponse(
            requesting_user_id=user_id,
            top_matches=top_matches,
            ranking_metadata=metadata.to_dict(),
        )
    except Exception as e:
        logger.error(f"Error calculating reciprocal matches for '{user_id}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to calculate matches.")
