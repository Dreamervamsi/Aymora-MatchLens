"""
Synthetic user profiles for testing and demonstrating MatchLens engine capabilities.
Contains realistic, entirely fictional adult profiles.
"""

from typing import Dict, List
from matchlens.models.profile import (
    UserProfile,
    UserAttributes,
    PartnerPreferences,
    Dealbreakers,
    DimensionWeights,
)
from matchlens.models.scenario import ScenarioResponse


def create_synthetic_profiles() -> Dict[str, UserProfile]:
    """
    Creates a set of diverse, fictional adult profiles for testing and demonstration.

    Profiles:
    - 'alex': Requesting user. Focused on core values, direct communication, long-term relationship.
    - 'taylor': High compatibility candidate. Aligned values, intent, and conflict resolution style.
    - 'jordan': Partial match candidate. Compatible intent and values, but divergent scenario preferences.
    - 'sam': Ineligible candidate. Fails relationship intention and age dealbreakers.
    - 'morgan': Incomplete profile candidate. Lacks core values and lifestyle answers -> pending information or low coverage.
    """
    alex = UserProfile(
        user_id="alex_101",
        attributes=UserAttributes(
            age=29,
            gender="man",
            relationship_intent="long_term",
            core_values=["honesty", "family", "ambition", "growth"],
            interests=["hiking", "reading", "cooking", "travel"],
            smoking="never",
            drinking="socially",
            exercise="weekly",
            has_children=False,
            wants_children="yes",
            communication_style="direct",
            conflict_resolution="cool_down_first",
            contact_frequency="daily_check_in",
        ),
        expectations=PartnerPreferences(
            min_age=24,
            max_age=34,
            acceptable_genders=["woman", "non-binary"],
            desired_intentions=["long_term", "marriage"],
            desired_values=["honesty", "family", "growth"],
            acceptable_smoking=["never"],
            acceptable_drinking=["never", "socially"],
            desired_wants_children=["yes", "open"],
            desired_communication_styles=["direct", "gentle"],
            desired_conflict_resolutions=["cool_down_first"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=True,
            strict_age_range=True,
            strict_gender_match=True,
            smoking_dealbreaker=True,
            children_dealbreaker=True,
            blocked_user_ids=[],
        ),
        weights=DimensionWeights(
            core_values=0.35,
            relationship_intentions=0.25,
            lifestyle_compatibility=0.15,
            communication_preferences=0.15,
            shared_interests=0.10,
        ),
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_resolution_01",
                target_dimension="communication_preferences",
                perspective="self_behavior",
                normalized_preference="cool_down_first",
                expected_partner_preference="cool_down_first",
                raw_answer="I like taking an hour to clear my head before talking through a dispute.",
                importance=1.5,
            ),
            ScenarioResponse(
                scenario_id="social_energy_01",
                target_dimension="lifestyle_compatibility",
                perspective="self_behavior",
                normalized_preference="small_group_gathering",
                expected_partner_preference="small_group_gathering",
                raw_answer="I prefer small dinners with close friends rather than massive parties.",
                importance=1.0,
            ),
        ],
    )

    taylor = UserProfile(
        user_id="taylor_202",
        attributes=UserAttributes(
            age=27,
            gender="woman",
            relationship_intent="long_term",
            core_values=["honesty", "family", "growth", "empathy"],
            interests=["hiking", "cooking", "yoga", "reading"],
            smoking="never",
            drinking="socially",
            exercise="weekly",
            has_children=False,
            wants_children="yes",
            communication_style="direct",
            conflict_resolution="cool_down_first",
            contact_frequency="daily_check_in",
        ),
        expectations=PartnerPreferences(
            min_age=25,
            max_age=35,
            acceptable_genders=["man"],
            desired_intentions=["long_term"],
            desired_values=["honesty", "ambition", "family"],
            acceptable_smoking=["never"],
            acceptable_drinking=["never", "socially"],
            desired_wants_children=["yes"],
            desired_communication_styles=["direct"],
            desired_conflict_resolutions=["cool_down_first"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=True,
            strict_age_range=True,
            strict_gender_match=True,
        ),
        weights=DimensionWeights(
            core_values=0.30,
            relationship_intentions=0.25,
            lifestyle_compatibility=0.20,
            communication_preferences=0.15,
            shared_interests=0.10,
        ),
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_resolution_01",
                target_dimension="communication_preferences",
                perspective="self_behavior",
                normalized_preference="cool_down_first",
                expected_partner_preference="cool_down_first",
                raw_answer="I definitely need a brief cool-down period before a calm conversation.",
                importance=1.5,
            ),
            ScenarioResponse(
                scenario_id="social_energy_01",
                target_dimension="lifestyle_compatibility",
                perspective="self_behavior",
                normalized_preference="small_group_gathering",
                expected_partner_preference="small_group_gathering",
                raw_answer="Small gatherings feel much more intimate and comfortable.",
                importance=1.0,
            ),
        ],
    )

    jordan = UserProfile(
        user_id="jordan_303",
        attributes=UserAttributes(
            age=28,
            gender="woman",
            relationship_intent="long_term",
            core_values=["honesty", "growth", "creativity"],
            interests=["travel", "music", "art"],
            smoking="never",
            drinking="socially",
            exercise="daily",
            has_children=False,
            wants_children="open",
            communication_style="expressive",
            conflict_resolution="discuss_immediately",
            contact_frequency="frequent",
        ),
        expectations=PartnerPreferences(
            min_age=25,
            max_age=35,
            acceptable_genders=["man"],
            desired_intentions=["long_term"],
            desired_values=["honesty", "growth"],
            acceptable_smoking=["never"],
            acceptable_drinking=["never", "socially"],
            desired_wants_children=["yes", "open"],
            desired_communication_styles=["expressive", "direct"],
            desired_conflict_resolutions=["discuss_immediately"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=True,
            strict_age_range=True,
            strict_gender_match=True,
        ),
        weights=DimensionWeights(
            core_values=0.30,
            relationship_intentions=0.25,
            lifestyle_compatibility=0.20,
            communication_preferences=0.15,
            shared_interests=0.10,
        ),
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_resolution_01",
                target_dimension="communication_preferences",
                perspective="self_behavior",
                normalized_preference="discuss_immediately",  # Divergent from Alex's expectation
                expected_partner_preference="discuss_immediately",
                raw_answer="I want to talk things through right away so nothing festers.",
                importance=1.5,
            ),
        ],
    )

    sam = UserProfile(
        user_id="sam_404",
        attributes=UserAttributes(
            age=42,  # Exceeds Alex's max_age preference (34)
            gender="woman",
            relationship_intent="casual",  # Conflicts with Alex's long_term dealbreaker
            core_values=["fun", "freedom"],
            interests=["partying", "travel"],
            smoking="regularly",  # Violates Alex's smoking dealbreaker
        ),
        expectations=PartnerPreferences(
            min_age=20,
            max_age=50,
            acceptable_genders=["man"],
            desired_intentions=["casual"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=True,
            strict_age_range=True,
        ),
    )

    morgan = UserProfile(
        user_id="morgan_505",
        attributes=UserAttributes(
            age=26,
            gender="woman",
            relationship_intent="long_term",
            # Lacks core_values, interests, lifestyle, and scenarios -> sparse profile
        ),
        expectations=PartnerPreferences(
            min_age=24,
            max_age=32,
            acceptable_genders=["man"],
            desired_intentions=["long_term"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=True,
        ),
    )

    return {
        "alex": alex,
        "taylor": taylor,
        "jordan": jordan,
        "sam": sam,
        "morgan": morgan,
    }
