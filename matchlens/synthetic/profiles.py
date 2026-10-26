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


"""
Synthetic user profiles for testing and demonstrating MatchLens engine capabilities.
Contains 10 diverse, fictional adult profiles with distinct interests, values, and lifestyle preferences.
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
    Creates a set of 10 diverse fictional adult profiles covering different interests and preferences.
    """
    p1_sarah = UserProfile(
        user_id="sarah_101",
        attributes=UserAttributes(
            age=27,
            gender="woman",
            relationship_intent="long_term",
            core_values=["honesty", "ambition", "curiosity"],
            interests=["tech", "gaming", "photography", "sci-fi"],
            smoking="never",
            drinking="socially",
            exercise="weekly",
            has_children=False,
            wants_children="open",
            communication_style="direct",
            conflict_resolution="discuss_immediately",
            contact_frequency="daily_check_in",
        ),
        expectations=PartnerPreferences(
            min_age=18,
            max_age=120,
            acceptable_genders=["man", "woman", "non-binary", "any"],
            desired_intentions=["long_term", "marriage", "casual", "friendship"],
            desired_values=["honesty", "ambition"],
            acceptable_smoking=["never", "socially"],
            acceptable_drinking=["never", "socially"],
            desired_wants_children=["yes", "open", "no", "maybe"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=False,
            strict_age_range=False,
            strict_gender_match=False,
        ),
    )

    p2_david = UserProfile(
        user_id="david_102",
        attributes=UserAttributes(
            age=30,
            gender="man",
            relationship_intent="long_term",
            core_values=["family", "integrity", "resilience"],
            interests=["hiking", "camping", "photography", "nature"],
            smoking="never",
            drinking="socially",
            exercise="daily",
            has_children=False,
            wants_children="yes",
            communication_style="gentle",
            conflict_resolution="cool_down_first",
            contact_frequency="daily_check_in",
        ),
        expectations=PartnerPreferences(
            min_age=18,
            max_age=120,
            acceptable_genders=["woman", "non-binary", "any"],
            desired_intentions=["long_term", "marriage"],
            desired_values=["family", "integrity"],
            acceptable_smoking=["never", "socially"],
            acceptable_drinking=["never", "socially"],
            desired_wants_children=["yes", "open"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=False,
            strict_age_range=False,
            strict_gender_match=False,
        ),
    )

    p3_elena = UserProfile(
        user_id="elena_103",
        attributes=UserAttributes(
            age=28,
            gender="woman",
            relationship_intent="long_term",
            core_values=["creativity", "authenticity", "empathy"],
            interests=["art", "music", "writing", "theater"],
            smoking="never",
            drinking="socially",
            exercise="weekly",
            has_children=False,
            wants_children="open",
            communication_style="expressive",
            conflict_resolution="discuss_immediately",
            contact_frequency="frequent",
        ),
        expectations=PartnerPreferences(
            min_age=18,
            max_age=120,
            acceptable_genders=["man", "woman", "non-binary", "any"],
            desired_intentions=["long_term", "marriage", "casual", "friendship"],
            desired_values=["creativity", "authenticity"],
            acceptable_smoking=["never", "socially"],
            acceptable_drinking=["never", "socially"],
            desired_wants_children=["yes", "open", "maybe"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=False,
            strict_age_range=False,
            strict_gender_match=False,
        ),
    )

    p4_marcus = UserProfile(
        user_id="marcus_104",
        attributes=UserAttributes(
            age=31,
            gender="man",
            relationship_intent="marriage",
            core_values=["discipline", "health", "loyalty"],
            interests=["fitness", "running", "sports", "cooking"],
            smoking="never",
            drinking="never",
            exercise="daily",
            has_children=False,
            wants_children="yes",
            communication_style="direct",
            conflict_resolution="discuss_immediately",
            contact_frequency="daily_check_in",
        ),
        expectations=PartnerPreferences(
            min_age=18,
            max_age=120,
            acceptable_genders=["woman", "non-binary", "any"],
            desired_intentions=["marriage", "long_term"],
            desired_values=["loyalty", "health"],
            acceptable_smoking=["never"],
            acceptable_drinking=["never", "socially"],
            desired_wants_children=["yes", "open"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=False,
            strict_age_range=False,
            strict_gender_match=False,
        ),
    )

    p5_maya = UserProfile(
        user_id="maya_105",
        attributes=UserAttributes(
            age=29,
            gender="woman",
            relationship_intent="long_term",
            core_values=["balance", "kindness", "growth"],
            interests=["cooking", "baking", "travel", "reading"],
            smoking="never",
            drinking="socially",
            exercise="weekly",
            has_children=False,
            wants_children="yes",
            communication_style="gentle",
            conflict_resolution="cool_down_first",
            contact_frequency="daily_check_in",
        ),
        expectations=PartnerPreferences(
            min_age=18,
            max_age=120,
            acceptable_genders=["man", "non-binary", "any"],
            desired_intentions=["long_term", "marriage"],
            desired_values=["kindness", "growth"],
            acceptable_smoking=["never", "socially"],
            acceptable_drinking=["never", "socially"],
            desired_wants_children=["yes", "open"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=False,
            strict_age_range=False,
            strict_gender_match=False,
        ),
    )

    p6_liam = UserProfile(
        user_id="liam_106",
        attributes=UserAttributes(
            age=26,
            gender="man",
            relationship_intent="long_term",
            core_values=["expression", "harmony", "curiosity"],
            interests=["music", "guitar", "concerts", "vinyl"],
            smoking="never",
            drinking="socially",
            exercise="weekly",
            has_children=False,
            wants_children="maybe",
            communication_style="expressive",
            conflict_resolution="discuss_immediately",
            contact_frequency="frequent",
        ),
        expectations=PartnerPreferences(
            min_age=18,
            max_age=120,
            acceptable_genders=["woman", "non-binary", "any"],
            desired_intentions=["long_term", "casual"],
            desired_values=["curiosity", "expression"],
            acceptable_smoking=["never", "socially"],
            acceptable_drinking=["never", "socially"],
            desired_wants_children=["open", "maybe"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=False,
            strict_age_range=False,
            strict_gender_match=False,
        ),
    )

    p7_chloe = UserProfile(
        user_id="chloe_107",
        attributes=UserAttributes(
            age=28,
            gender="non-binary",
            relationship_intent="long_term",
            core_values=["wisdom", "kindness", "authenticity"],
            interests=["reading", "gardening", "philosophy", "yoga"],
            smoking="never",
            drinking="never",
            exercise="weekly",
            has_children=False,
            wants_children="no",
            communication_style="analytical",
            conflict_resolution="written_first",
            contact_frequency="as_needed",
        ),
        expectations=PartnerPreferences(
            min_age=18,
            max_age=120,
            acceptable_genders=["man", "woman", "non-binary", "any"],
            desired_intentions=["long_term", "marriage", "casual", "friendship"],
            desired_values=["kindness", "authenticity"],
            acceptable_smoking=["never", "socially"],
            acceptable_drinking=["never", "socially"],
            desired_wants_children=["no", "open"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=False,
            strict_age_range=False,
            strict_gender_match=False,
        ),
    )

    p8_noah = UserProfile(
        user_id="noah_108",
        attributes=UserAttributes(
            age=32,
            gender="man",
            relationship_intent="long_term",
            core_values=["adventure", "courage", "growth"],
            interests=["travel", "scuba diving", "hiking", "skiing"],
            smoking="never",
            drinking="socially",
            exercise="daily",
            has_children=False,
            wants_children="yes",
            communication_style="direct",
            conflict_resolution="discuss_immediately",
            contact_frequency="daily_check_in",
        ),
        expectations=PartnerPreferences(
            min_age=18,
            max_age=120,
            acceptable_genders=["woman", "non-binary", "any"],
            desired_intentions=["long_term", "marriage"],
            desired_values=["growth", "adventure"],
            acceptable_smoking=["never", "socially"],
            acceptable_drinking=["never", "socially"],
            desired_wants_children=["yes", "open"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=False,
            strict_age_range=False,
            strict_gender_match=False,
        ),
    )

    p9_sophia = UserProfile(
        user_id="sophia_109",
        attributes=UserAttributes(
            age=27,
            gender="woman",
            relationship_intent="marriage",
            core_values=["sustainability", "compassion", "family"],
            interests=["nature", "volunteering", "gardening", "hiking"],
            smoking="never",
            drinking="never",
            exercise="weekly",
            has_children=False,
            wants_children="yes",
            communication_style="gentle",
            conflict_resolution="cool_down_first",
            contact_frequency="daily_check_in",
        ),
        expectations=PartnerPreferences(
            min_age=18,
            max_age=120,
            acceptable_genders=["man", "non-binary", "any"],
            desired_intentions=["marriage", "long_term"],
            desired_values=["family", "compassion"],
            acceptable_smoking=["never", "socially"],
            acceptable_drinking=["never", "socially"],
            desired_wants_children=["yes", "open"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=False,
            strict_age_range=False,
            strict_gender_match=False,
        ),
    )

    p10_ethan = UserProfile(
        user_id="ethan_110",
        attributes=UserAttributes(
            age=29,
            gender="man",
            relationship_intent="casual",
            core_values=["fun", "independence", "honesty"],
            interests=["gaming", "movies", "podcasts", "tech"],
            smoking="socially",
            drinking="socially",
            exercise="rarely",
            has_children=False,
            wants_children="no",
            communication_style="expressive",
            conflict_resolution="discuss_immediately",
            contact_frequency="as_needed",
        ),
        expectations=PartnerPreferences(
            min_age=18,
            max_age=120,
            acceptable_genders=["woman", "man", "non-binary", "any"],
            desired_intentions=["casual", "friendship", "long_term"],
            desired_values=["fun", "honesty"],
            acceptable_smoking=["never", "socially", "regularly"],
            acceptable_drinking=["never", "socially", "regularly"],
            desired_wants_children=["no", "open"],
        ),
        dealbreakers=Dealbreakers(
            strict_intention_match=False,
            strict_age_range=False,
            strict_gender_match=False,
        ),
    )

    return {
        "sarah": p1_sarah,
        "david": p2_david,
        "elena": p3_elena,
        "marcus": p4_marcus,
        "maya": p5_maya,
        "liam": p6_liam,
        "chloe": p7_chloe,
        "noah": p8_noah,
        "sophia": p9_sophia,
        "ethan": p10_ethan,
    }
