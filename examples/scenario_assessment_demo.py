#!/usr/bin/env python3
"""
CLI Demonstration for Phase 5.3: Scenario-Based Relationship Assessment
"""
import asyncio
import sys
from matchlens.assessment import (
    ScenarioAssessmentOrchestrator,
    AssessmentStatus,
    AssessmentStage,
    attach_scenario_responses,
)
from matchlens.models.profile import UserProfile, UserAttributes, PartnerPreferences
from matchlens.engine.reciprocal import calculate_reciprocal_match


async def run_assessment_demo():
    print("=" * 70)
    print("   MatchLens — Phase 5.3: Scenario-Based Assessment CLI Demo")
    print("=" * 70)

    orchestrator = ScenarioAssessmentOrchestrator()

    user_id = "user_demo_alex"
    print(f"\n[1] Initializing Scenario Assessment for user: '{user_id}'...")

    selected_scenarios = [
        "conflict_resolution_01",
        "social_energy_01",
        "financial_planning_01",
    ]

    turn = orchestrator.start_assessment(user_id=user_id, selected_scenario_ids=selected_scenarios)
    aid = turn.assessment_id

    # Simulated inputs for self behavior and partner expectations
    answers = [
        # conflict_resolution_01
        "cool_down_first",        # Self: cool down first
        "discuss_immediately",   # Partner: discuss immediately

        # social_energy_01
        "small_group_gathering", # Self: small group
        "small_group_gathering", # Partner: small group

        # financial_planning_01
        "balanced_spending",     # Self: balanced spending
        "strict_savings_first",  # Partner: strict savings first
    ]

    for user_input in answers:
        print("\n" + "-" * 50)
        print(turn.prompt_text)
        print("-" * 50)
        print(f"--> User Inputs Choice: '{user_input}'")

        turn = await orchestrator.submit_response(aid, user_input)

        if turn.unresolved_clarification:
            print(f"[!] AI requested clarification: {turn.unresolved_clarification.clarification_prompt}")

    # Review stage
    if turn.status == AssessmentStatus.READY_FOR_REVIEW:
        print("\n" + "=" * 70)
        print("   ASSESSMENT COMPLETE - REVIEW STAGE")
        print("=" * 70)
        print(turn.prompt_text)
        print("\nSummary of Collected Responses:")
        for sid, data in turn.summary_data.items():
            print(f"  • {sid}: Self -> {data['self_response']} | Partner Expected -> {data['partner_expectation']}")

        print("\n[2] Confirming assessment...")
        turn = orchestrator.confirm_assessment(aid)
        print(f"Final Status: {turn.status.value}")

    # Convert to canonical ScenarioResponse objects
    canonical_responses = orchestrator.get_completed_responses(aid)
    print(f"\nGenerated {len(canonical_responses)} canonical ScenarioResponse objects.")

    # Create user profile and attach responses
    alex_profile = UserProfile(
        user_id="alex_demo",
        attributes=UserAttributes(
            age=29, gender="non-binary", relationship_intent="long_term",
            core_values=["family", "honesty"], communication_style="direct", conflict_resolution="cool_down_first"
        ),
        expectations=PartnerPreferences(
            min_age=25, max_age=35, acceptable_genders=["any"],
            desired_intentions=["long_term"], desired_conflict_resolutions=["discuss_immediately", "cool_down_first"]
        )
    )

    alex_updated_profile = attach_scenario_responses(alex_profile, canonical_responses)
    print(f"Alex Profile successfully updated. Total scenarios attached: {len(alex_updated_profile.scenarios)}")

    # Create prospective match profile (Jordan)
    jordan_profile = UserProfile(
        user_id="jordan_demo",
        attributes=UserAttributes(
            age=31, gender="woman", relationship_intent="long_term",
            core_values=["family", "honesty"], communication_style="direct", conflict_resolution="discuss_immediately"
        ),
        expectations=PartnerPreferences(
            min_age=26, max_age=36, acceptable_genders=["any"],
            desired_intentions=["long_term"], desired_conflict_resolutions=["cool_down_first"]
        )
    )

    # Attach complementary scenario responses for Jordan
    from matchlens.models.scenario import ScenarioResponse
    jordan_scenarios = [
        ScenarioResponse(
            scenario_id="conflict_resolution_01", target_dimension="communication_preferences",
            perspective="self_behavior", normalized_preference="discuss_immediately", expected_partner_preference="cool_down_first"
        ),
        ScenarioResponse(
            scenario_id="social_energy_01", target_dimension="lifestyle_compatibility",
            perspective="self_behavior", normalized_preference="small_group_gathering", expected_partner_preference="small_group_gathering"
        ),
        ScenarioResponse(
            scenario_id="financial_planning_01", target_dimension="core_values",
            perspective="self_behavior", normalized_preference="strict_savings_first", expected_partner_preference="balanced_spending"
        ),
    ]
    jordan_updated_profile = attach_scenario_responses(jordan_profile, jordan_scenarios)

    # Run reciprocal matching engine
    print("\n[3] Running Reciprocal Compatibility Engine between Alex and Jordan...")
    match_result = calculate_reciprocal_match(alex_updated_profile, jordan_updated_profile)

    print(f"\n>>> Reciprocal Mutual Compatibility Score: {match_result.mutual_score:.1f}% <<<")
    print(f"    Eligibility: {match_result.eligibility_status}")
    print(f"    Evidence Coverage: {match_result.evidence_coverage:.1f}%")

    print("\nScenario Evidence Highlights:")
    if match_result.evidence_summary and match_result.evidence_summary.scenario_highlights:
        for hl in match_result.evidence_summary.scenario_highlights:
            print(f"  ✓ {hl}")

    print("\n" + "=" * 70)
    print("   Scenario Assessment Phase 5.3 CLI Demo Completed Successfully")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_assessment_demo())
