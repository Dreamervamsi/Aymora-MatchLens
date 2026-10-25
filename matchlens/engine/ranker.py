"""
Candidate ranking engine for MatchLens.
Filters candidates by eligibility and evidence coverage, then ranks by mutual score with deterministic tie-breaking.
"""

import math
from typing import List, Tuple, Dict, Any, Set
from matchlens.models.profile import UserProfile
from matchlens.models.scoring import MatchResult
from matchlens.engine.reciprocal import calculate_reciprocal_match
from matchlens.config import DEFAULT_MIN_EVIDENCE_COVERAGE


class RankingMetaData:
    """
    Summary metrics regarding candidate ranking execution.
    """
    def __init__(
        self,
        total_candidates: int,
        eligible_candidates: int,
        pending_information_candidates: int,
        filtered_for_coverage: int,
        returned_count: int,
    ):
        self.total_candidates = total_candidates
        self.eligible_candidates = eligible_candidates
        self.pending_information_candidates = pending_information_candidates
        self.filtered_for_coverage = filtered_for_coverage
        self.returned_count = returned_count

    def to_dict(self) -> Dict[str, int]:
        return {
            "total_candidates": self.total_candidates,
            "eligible_candidates": self.eligible_candidates,
            "pending_information_candidates": self.pending_information_candidates,
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

    Input Validations:
    - top_k must be an integer > 0.
    - min_evidence_coverage must be a finite float between 0.0 and 100.0.

    Deduplication:
    - Candidates with duplicate user IDs are deduplicated, preserving the first occurrence.

    Returns (top_matches, ranking_metadata).
    """
    if top_k <= 0:
        raise ValueError(f"top_k must be a positive integer greater than 0, got {top_k}.")

    if not math.isfinite(min_evidence_coverage) or not (0.0 <= min_evidence_coverage <= 100.0):
        raise ValueError(
            f"min_evidence_coverage must be a finite float between 0.0 and 100.0, got {min_evidence_coverage}."
        )

    # Deduplicate candidate profiles by user_id
    seen_ids: Set[str] = set()
    deduped_candidates: List[UserProfile] = []
    for cand in candidates:
        if cand.user_id not in seen_ids:
            seen_ids.add(cand.user_id)
            deduped_candidates.append(cand)

    total_candidates = len(deduped_candidates)
    eligible_count = 0
    pending_info_count = 0
    coverage_filtered_count = 0

    all_results: List[MatchResult] = []

    for candidate in deduped_candidates:
        match_res = calculate_reciprocal_match(
            user_a=requesting_user,
            user_b=candidate,
            min_evidence_coverage=min_evidence_coverage,
        )

        if match_res.eligibility_status == "pending_information":
            pending_info_count += 1
            continue
        elif not match_res.is_eligible:
            continue

        eligible_count += 1

        if match_res.is_low_coverage and not include_low_coverage:
            coverage_filtered_count += 1
            continue

        all_results.append(match_res)

    # Deterministic Sort Hierarchy:
    # 1. mutual_score (descending)
    # 2. evidence_coverage (descending)
    # 3. candidate user_b_id (alphabetical ascending)
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
        pending_information_candidates=pending_info_count,
        filtered_for_coverage=coverage_filtered_count,
        returned_count=len(top_matches),
    )

    return top_matches, metadata
