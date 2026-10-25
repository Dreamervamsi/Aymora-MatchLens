"""
Candidate ranking engine for MatchLens.
Filters candidates by eligibility and evidence coverage, then ranks by mutual score with deterministic tie-breaking.
"""

from typing import List, Tuple, Dict, Any
from matchlens.models.profile import UserProfile
from matchlens.models.scoring import MatchResult
from matchlens.engine.reciprocal import calculate_reciprocal_match
from matchlens.config import DEFAULT_MIN_EVIDENCE_COVERAGE


class RankingMetaData:
    """
    Summary metrics regarding the candidate ranking execution.
    """
    def __init__(
        self,
        total_candidates: int,
        eligible_candidates: int,
        filtered_for_coverage: int,
        returned_count: int,
    ):
        self.total_candidates = total_candidates
        self.eligible_candidates = eligible_candidates
        self.filtered_for_coverage = filtered_for_coverage
        self.returned_count = returned_count

    def to_dict(self) -> Dict[str, int]:
        return {
            "total_candidates": self.total_candidates,
            "eligible_candidates": self.eligible_candidates,
            "filtered_for_coverage": self.filtered_for_coverage,
            "returned_count": self.returned_count,
        }


def rank_candidates(
    requesting_user: UserProfile,
    candidates: List[UserProfile],
    top_k: int = 3,
    min_evidence_coverage: float = DEFAULT_MIN_EVIDENCE_COVERAGE,
    include_low_coverage: bool = False,
) -> Tuple[List[MatchResult], RankingMetaData]:
    """
    Evaluates, filters, and ranks candidate profiles for requesting_user.

    Steps:
    1. For each candidate in candidates collection:
       - Calculate reciprocal match score and evidence breakdown.
    2. Filter candidates:
       - Exclude candidates with is_eligible == False (dealbreaker violation or self-matching).
       - Exclude candidates with evidence_coverage < min_evidence_coverage unless include_low_coverage=True.
    3. Deterministic Sort Hierarchy:
       - Primary: mutual_score (descending, None treated as 0.0)
       - Secondary: evidence_coverage (descending)
       - Tertiary: candidate user_b_id (alphabetical ascending for deterministic tie-breaking)
    4. Slice top K matches.

    Returns (top_matches, ranking_metadata).
    """
    total_candidates = len(candidates)
    eligible_count = 0
    coverage_filtered_count = 0

    all_results: List[MatchResult] = []

    for candidate in candidates:
        match_res = calculate_reciprocal_match(
            user_a=requesting_user,
            user_b=candidate,
            min_evidence_coverage=min_evidence_coverage,
        )

        if not match_res.is_eligible:
            continue

        eligible_count += 1

        if match_res.is_low_coverage and not include_low_coverage:
            coverage_filtered_count += 1
            continue

        all_results.append(match_res)

    # Sort hierarchy
    # Key sorting tuple:
    # 1. -(mutual_score or 0.0)
    # 2. -evidence_coverage
    # 3. user_b_id (alphabetical)
    sorted_results = sorted(
        all_results,
        key=lambda r: (
            -(r.mutual_score if r.mutual_score is not None else -1.0),
            -r.evidence_coverage,
            r.user_b_id,
        ),
    )

    top_matches = sorted_results[:top_k]

    metadata = RankingMetaData(
        total_candidates=total_candidates,
        eligible_candidates=eligible_count,
        filtered_for_coverage=coverage_filtered_count,
        returned_count=len(top_matches),
    )

    return top_matches, metadata
