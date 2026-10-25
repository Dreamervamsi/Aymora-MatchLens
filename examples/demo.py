#!/usr/bin/env python3
"""
MatchLens Core Reciprocal Compatibility Engine Demonstration.
Executes mutual eligibility, directional scoring, reciprocal geometric mean aggregation,
structured evidence extraction, candidate ranking, and preference weight sensitivity.
"""

import json
from matchlens.synthetic.profiles import create_synthetic_profiles
from matchlens.engine.reciprocal import calculate_reciprocal_match
from matchlens.engine.ranker import rank_candidates
from matchlens.models.profile import DimensionWeights


def main():
    print("=" * 80)
    print("           AYMORA MATCHLENS — RECIPROCAL COMPATIBILITY ENGINE DEMO           ")
    print("=" * 80)

    profiles = create_synthetic_profiles()
    alex = profiles["alex"]
    taylor = profiles["taylor"]
    jordan = profiles["jordan"]
    sam = profiles["sam"]
    morgan = profiles["morgan"]

    # 1. Pair Evaluation: Alex & Taylor (High Compatibility)
    print("\n--- 1. SINGLE PAIR EVALUATION: Alex & Taylor ---")
    match_res = calculate_reciprocal_match(alex, taylor)

    print(f"User A: {match_res.user_a_id} | User B: {match_res.user_b_id}")
    print(f"Eligibility Status: {match_res.eligibility_status} (is_eligible={match_res.is_eligible})")
    print(f"Directional Score (Alex -> Taylor): {match_res.directional_a_to_b.directional_score} / 100.0")
    print(f"Directional Score (Taylor -> Alex): {match_res.directional_b_to_a.directional_score} / 100.0")
    print(f"Reciprocal Score S_mutual(Alex, Taylor): {match_res.mutual_score} / 100.0")
    print(f"Evidence Coverage: {match_res.evidence_coverage}% (is_low_coverage={match_res.is_low_coverage})")

    if match_res.evidence_summary:
        print("\nStructured Evidence Summary:")
        print(f"  Shared Strengths ({len(match_res.evidence_summary.strengths)}):")
        for s in match_res.evidence_summary.strengths[:3]:
            print(f"    + {s}")
        print(f"  Scenario Highlights ({len(match_res.evidence_summary.scenario_highlights)}):")
        for sc in match_res.evidence_summary.scenario_highlights:
            print(f"    * {sc}")

    # 2. Pair Evaluation: Alex & Sam (Ineligible Dealbreaker Failure)
    print("\n--- 2. DEALBREAKER EVALUATION: Alex & Sam ---")
    sam_match = calculate_reciprocal_match(alex, sam)
    print(f"Eligibility Status: {sam_match.eligibility_status} (is_eligible={sam_match.is_eligible})")
    print("Ineligibility Reasons:")
    for r in sam_match.ineligibility_reasons:
        print(f"  - {r}")

    # 3. Top-K Candidate Ranking
    candidates = [taylor, jordan, sam, morgan]
    print("\n--- 3. CANDIDATE RANKING FOR ALEX (Default Weights) ---")
    print("Alex's Default Weights: Core Values 35%, Intentions 25%, Lifestyle 15%, Comm 15%, Interests 10%")

    top_matches, meta = rank_candidates(
        requesting_user=alex,
        candidates=candidates,
        top_k=3,
        min_evidence_coverage=50.0,
    )

    print(f"\nRanking Metadata: {meta.to_dict()}")
    print("\nRanked Candidates:")
    for rank, match in enumerate(top_matches, start=1):
        print(
            f"  Rank {rank}: {match.user_b_id} | Mutual Score: {match.mutual_score} | "
            f"Directional (A->B): {match.directional_a_to_b.directional_score} | "
            f"Directional (B->A): {match.directional_b_to_a.directional_score} | "
            f"Coverage: {match.evidence_coverage}%"
        )

    # 4. Weight Sensitivity Demonstration
    print("\n--- 4. WEIGHT SENSITIVITY DEMO: Shift Alex's Weights to Communication & Shared Interests ---")
    alex_modified = alex.model_copy(deep=True)
    alex_modified.weights = DimensionWeights(
        core_values=0.05,
        relationship_intentions=0.05,
        lifestyle_compatibility=0.10,
        communication_preferences=0.40,
        shared_interests=0.40,
    )

    top_matches_mod, meta_mod = rank_candidates(
        requesting_user=alex_modified,
        candidates=candidates,
        top_k=3,
        min_evidence_coverage=50.0,
    )

    print(f"\nRanking Metadata (Modified Weights): {meta_mod.to_dict()}")
    print("\nRanked Candidates with Modified Weights:")
    for rank, match in enumerate(top_matches_mod, start=1):
        print(
            f"  Rank {rank}: {match.user_b_id} | Mutual Score: {match.mutual_score} | "
            f"Directional (Alex->B): {match.directional_a_to_b.directional_score} | "
            f"Directional (B->Alex): {match.directional_b_to_a.directional_score}"
        )

    print("\n" + "=" * 80)
    print("                  DEMO COMPLETED SUCCESSFULLY!                  ")
    print("=" * 80)


if __name__ == "__main__":
    main()
